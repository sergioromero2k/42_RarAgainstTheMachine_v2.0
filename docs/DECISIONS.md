# Decisiones de diseño

## Configuración de proyecto: `uv over pip/installs`
* `uv` está escrito en Rust, no en Python puro como `pip`. Usa caché global de paquetes y resolución de dependencias en paralelo, así que instalar o sincronizar dependencias es órdenes de magnitud más rápido.
* Con `pip` normalmente necesitas tres herramientas separadas — `venv` (crear el entorno), `pip` (instalar paquetes) y a veces `pip-tools` (generar lockfile). `uv` hace las tres cosas con un solo comando (`uv sync`), y genera automáticamente `uv.lock` — un `lockfile` que fija versiones exactas de todo el árbol de dependencias, para que el proyecto se reproduzca igual en cualquier máquina (la del evaluador, por ejemplo).

Esto se usa en 42 por que es mas fácil, si tu compañero clona el repo y hace `uv sync`, tiene que instalarse exactamente lo mismo que tú, sin sopresas de versiones.

## Pydantic models vs service class
* `BaseModel` sirve para validación automática al crear la instancia: si declaras `first_character_index: int` y alguien inerna crear el modelo con un string, Pydantic lanza un `ValidationError` automáticamente, sin que tú escribas ningún `if isinstance(...)`. Tambien permite la serialización/deserialización gratis `.model_dump_json()` convierte la instancia a JSON, `.model_validate_json()` hace el camino inverso. Esto es oro para tu proyecto, porque constantemente guardas/cargas cosas a disco (el dataset, los resultados de búsqueda, etc.) — sin Pydantic tendrías que escribir ese parseo a mano.
* `BaseModel` está pensado para **estructura de datos** cosas que principalmente se guardan, se cargan, se validan y se serializan a/desde  JSON. Su fortaleza es garantizar que los datos tienen la forma correcta.
* Los 8 modelos son todos estructuras de datos puras, se leen de JSON, se escriben en JSON, no tienen comportamiento propio. Por eso todos heredan de `BaseModel`, sin excepción.

### Models
* `MinimalSource` un fragmento de archivo: `ruta` + `índice de carácter`. Es el bloque atómica que usan casi todos los demás modelos para citar de dónde sale la información.
* `UnansweredQuestion` — una pregunta sin responder: question_id (autogenerado con default_factory, como ya vimos) + el texto. Es la entrada "cruda" del dataset.
* `AnsweredQuestion(UnansweredQuestion)` — hereda de la anterior porque es una pregunta, pero con extras: `sources` (dónde está la respuesta real) y `answer`.
* `RagDataset` el contenedor del `dataset` completo: una lista de preguntas que pueden ser `AnsweredQuestion` o `UnansweredQuestion` (con el |, un `Union`). 
* `MinimalSearchResults` — el resultado de buscar **(no responder)** una pregunta: su `question_id`, el texto, y los `retrieved_sources` que encontró tu `Retriever`.
* `MinimalAnswer(MinimalSearchResults)` hereda porque además de los resultados de búsqueda, añade el campo `answer` generado por el **LLM**. Mismo patrón que `AnsweredQuestion`/`UnansweredQuestion`: "es un resultado de búsqueda + la respuesta generada".
* `StudentSearchResults` el resultado de correr `search_dataset` sobre todo el dataset: una lista de `MinimalSearchResults` + el `k` usado. Es el contenedor de nivel superior, no una pregunta individual.
* `StudentSearchResultsAndAnswer(StudentSearchResults)` — hereda de `StudentSearchResults`, pero sobrescribe search_results para que ahora sea una lista de `MinimalAnswer` (con respuesta) en vez de `MinimalSearchResults` (sin respuesta).

## Ingestion & Indexer
`Ingestion` se encarga de **leer el repositorio de vLLM y trocearlo.**
Concretamente:
* Si el repo no está descomprimido en disco, lo descomprime automáticamente (`ensure_repo_extracted()`).
* Recorre todos los archivos del repo(`rglob`), filtrando solo `.py`, `.md`, `.txt`.
* Para cada archivo, elige el chunker correcto según su extensión, y lo trocea en fragmentos (`MinimalSource` + el texto real de ese fragmento).
* Devuelve la lista completa de (`MinimalSource`, texto) de todo el repo.

`Indexer` se encarga de **construir**, **guardar** y **cargar** el índice de búsqueda `BM25` a partir de esos chunks. 
Concretamente:
* `build_index()` coge la lista de `(MinimalSource, texto)` que le da `Ingestion`, separa los textos de los metadatos en 2 listas, paralelas, tokeniza los textos, y construye el índice BM25 con `bm25s`.
* `save()`: guarda ese índice y la lista de metadatos a disco (**data/processed/**).
* `load()`: recupera ambas cosas desde disco para usarlas de nuevo sin tener que reconstruir todo.

## Indexer & Retriever
* `Indexer` responsable de **construir y persistir** el índice de búsqueda: toma los chunks ya troceados, los tokeniza, construye el índice **BM25** en memoria, y lo guarda/carga de disco (`build_index()`, `save()`, `load()`). Es la parte **"offline"** del sistema - se ejecuta una vez (en el comando `index`), no en cada búsqueda.

* `Retriever` responsable de **buscar en tiempo real** sobre un índice ya construido: recibe el `bm25_index` y `sources_metadata` ya cargados, tokeniza la `query` del usuario de la misma forma que se tokenizó al `indexar`, y devuelve los top-k `MinimalSource` más relevantes. Es la parte **"online"** — se ejecuta en cada llamada a `search()`, `Retriever` no responde, solo recupera — te da una lista ordenada de los chunks más relevantes (como fragmentos de evidencia), y nada más. Esa lista luego la usan otras piezas: tú mismo la usas directamente en el comando **search()** (para enseñarle al evaluador qué encontró), y más adelante `Generator` la usa como contexto para redactar la respuesta en lenguaje natural con **Qwen3**.

### Ejemplo
* `Ingestion` es la que va primero: abre el repo de vLLM (lo descomprime si hace falta), recorre todos los archivos `.py`, `.md` y `.txt`, y a cada uno lo trocea con su chunker. Devuelve una lista de pares: el `MinimalSource` (archivo + dónde empieza y acaba el trozo) y el texto de ese trozo. No busca nada ni construye ningún índice, solo prepara los trozos.
* `Indexer` coge esos trozos, tokeniza los textos y hace algo como un diccionario: palabra -> en qué chunks sale y cuántas veces. Eso se guarda tal cual en el índice.
* `Retriever` coge la pregunta, la tokeniza igual, mira ese diccionario a ver qué chunks tienen más coincidencia con las palabras de la pregunta, y devuelve los **top-k**. No da respuesta, solo busca y trae lo más parecido.

Orden: `Ingestion` (trocea) -> `Indexer` (indexa) -> `Retriever` (busca).

## search_dataset
`search()` responde a una pregunta suelta, pensada para probar a mano desde la terminal. Pero con una sola pregunta no puedes saber si tu sistema es bueno. Para eso necesitas medirlo con muchas preguntas, y `search_dataset` es lo que permite medirlo.

* El dataset (`dataset_docs_public.json`) es una lista de preguntas, por ejemplo 100.
* `search_dataset` le hace todas esas preguntas a tu `Retriever` y apunta, para cada una, qué chunks ha recuperado.
* Guarda todo en un archivo JSON(`StudentSearchResults`). Ese archivo es tu **tu hoja de respuestas del examen.**
* Luego alguien corrige esa hoja comparándola con las respuestas correctas (el dataset `AnsweredQuestions`): la `moulinette` en la defensa, y tu propio evaluate (el Día 10) mientras desarrollas. De ahí sale el **recall@k**.

**Tunnig(ajuste, o afinado)** es cambiar los parámetros o decisiones de tu sistema para que acierte más, midiendo el efecto de cada cambio. Un ejemplo con tu proyecto: pruebas `max_chunk_size=2000`, mides el recall, lo bajas a 1000, vuelves a medir y te quedas con el que dé mejor resultado.

## IoU (Intersection over Union)
* El **IoU** **no** compara respuestas escritas, compara sitios del archivo.
* **IoU** no es un algoritmo complejo, es una métrica: una fórmula que da un número entre 0 y 1 para decir cuánto se parecen dos cosas. Se calcula en tres operaciones (mínimo, máximo, una división). También se llama índice de Jaccard (lo propuso Paul Jaccard a principios del siglo XX para comparar conjuntos). Tu caso es la versión más simple: en vez de cuadros en 2D, son rangos en una línea (casillas de un archivo, 1D).

Es la medida de cuánto se solapan dos rangos de caracteres: la parte común dividida por la parte total que cubren entre los dos. Vale 1 si coinciden del todo y 0 si no se tocan. En este proyecto se usa para decidir si un `chunk` tuyo "acierta" respecto al fragmento correcto del dataset.

* **Lo que ellos te dan:** para cada pregunta, el lugar exacto donde está la información. Por ejemplo, "en lora.md, casillas 4695 a 6098".
* **Lo que genera tu sistema:** para cada pregunta, 10 trozos que cree que contienen la información. Cada uno con su archivo y sus casillas.
* **Lo que mide el IoU:** si alguno de tus 10 trozos cae en el mismo sitio que el de ellos.

### Ejemplo de cálculo de IoU en `lora.md`
- **Fragmento correcto (dataset):** posiciones 100–200.
- **Fragmento predicho (sistema):** posiciones 150–250.

**Paso 1. Calcular la intersección**
Ambos fragmentos comparten las posiciones 150–200.
* **Intersección** = 200 - 150 = 50

**Paso 2. Calcular la unión**
El rango total que cubren ambos fragmentos va de la posición 100 a la 250.
* **Unión** = 250 - 100 = 150

**Paso 3. Calcular el IoU**
La fórmula es: `IoU = Intersección / Unión`
Sustituyendo los valores: `IoU = 50 / 150 = 0.33`

**Resultado:** el IoU es aproximadamente `0.33`, lo que indica que existe un solapamiento parcial entre el fragmento correcto y el fragmento predicho.

### Corpus
Corpus es simplemente el conjunto completo de todos los textos sobre los que vas a buscar, En tu proyecto, el corpus es: **todos los chunks (trozos)** de todos los archivo `.py` y `.md` del repositorio de vLLM, ya troceados.

### Indexar
Procesar ese corpus por adelantado para poder buscar en él rápido después, en vez de tener que releer y analizar todo cada vez que alguien pregunta algo. Es la misma idea que el índice de un libro: en vez de leer las 400 páginas cada vez que buscas dónde se habla de “mitocondrias”, el libro tiene un índice al final que dice “mitocondrias: página 145, 203, 310” — construido una vez, usado muchas veces.

### Tokenizar
Partir un texto en piezas más pequeñas (normalmente palabras) para poder trabajar con ellas por separado, en vez de tratar el texto como un bloque único.

Ejemplo:
```py
texto = "How to configure the OpenAI server?"
tokens = ["how", "to", "configure", "the", "openai", "server"]
```
### stemming
Reducir plaabras a su raíz, quitando sufijos, para que variantes de una misma palabra cuenten como "la misma" al buscar.
Ejemplo:
```
"retrieving"  → "retriev"
"retrieved"   → "retriev"
"retriever"   → "retriev"
"retrieval"   → "retriev"
```
Todas se reducen a la misma raíz **"retriev"**. ¿Por qué importa? Porque si el corpus tiene la palabra **"retrieval"** y el usuario en su query escribe **"retrieving"**, sin stemming BM25 las trataría como palabras completamente distintas (son strings diferentes) y no encontraría la coincidencia — aunque para un humano sea obviamente la misma idea.

### tqdm
Es una librería que muestra una **barra de progresa** en el terminal. Ahora mismo, cunado lanzas `search_dataset`, la terminal se queda en blanco hasta el final y no sabes si va bien o se ha colgado. Con tqdm ves algo así:

42%|████████▌          | 42/100 [00:12<00:16,  3.5it/s]


## Valor por defecto de save_directory

**Decisión:** `data/output/search_results`.
**Por qué:** es una ruta real, funciona sin argumentos y queda dentro de `data/output/` (ignorada por git).
**Limitación:** si lanzo dos datasets con el mismo nombre desde carpetas distintas sin pasar subcarpeta, el segundo sobrescribe al primero. Por eso, al medir, paso `--save_directory` con la subcarpeta del tipo de dataset.

### Unanswered
**Dataset** es simplemente un archivo JSON con una lista de preguntas. 
Tienes dos versiones del mismo, y las dos están en `data/datasets/`:

* `UnansweredQuestions/dataset_docs_public.json`: las preguntas sin la respuesta correcta. Solo trae el texto de cada pregunta y su question_id. Es lo que le das a tu sistema para que busque.
* `AnsweredQuestions/dataset_docs_public.json`: las mismas preguntas, pero con la respuesta correcta incluida (la fuente donde está, y la respuesta en texto). Es la “hoja de soluciones”, y la usará el evaluador.

Por eso:
* `search_dataset` usa el `Unanswered`, porque tu buscador no debe ver la solución.
* `evaluate` usa el `Answered`, porque necesita saber cuál era la solución para compararla con lo que encontraste.

Los dos modelos que necesitas:

* Para leer **tus resultados**: `StudentSearchResults`. Es el mismo que usaste en `search_dataset` para guardarlos, y de él sacas `search_results` (una lista con un elemento por pregunta, cada uno con question_id y retrieved_sources).
* Para leer **el dataset con respuestas**: `RagDataset`. De él sacas `rag_questions`.

### sources
Es la lista de fuentes correctas de una pregunta: la “solución”, con ruta y caracteres. Solo existe en `AnsweredQuestion`. La `UnansweredQuestion` solo trae el texto de la pregunta y su `question_id`.


## evaluator
| Función | Responde a | Usa |
|---|---|---|
| `iou` | ¿Cuánto se solapan dos rangos de caracteres? | Nada |
| `is_match` | ¿Este chunk tuyo y esta fuente correcta coinciden? (mismo archivo + IoU ≥ 0.05) | `iou` |
| `hit_at_k` | ¿Alguno de tus primeros k chunks coincide con alguna fuente correcta? | `is_match` |
| `build_results_index` | Acceso rápido a tus chunks por `question_id` | Nada |
| `recall_at_k` | ¿Qué porcentaje de preguntas tiene acierto? | `hit_at_k` + `build_results_index` |

#### `results` (lo que TÚ encontraste):
  pregunta **"How does LoRA...?"**  →  [chunk A, chunk B, chunk C, ...]

#### `dataset` (la respuesta correcta de ELLOS):
  pregunta **"How does LoRA...?"**  →  sources = [lora.md 4695-6098]

* **Tuning** es justo lo que dices, con un matiz: no es reescribir el programa, sino ajustar parámetros y pequeñas decisiones y volver a medir para ver si el número sube.

## Day 11 - Tabla
| Dataset              | @1   | @3   | @5   | @10  |
|----------------------|-----:|-----:|-----:|-----:|
| docs (100 preguntas) | 54.0 | 76.0 | 81.0 | 89.0 |
| code (99 preguntas)  | 32.3 | 46.5 | 51.5 | 62.6 |

## source_recall_at_k
Cambiar el recall a fracción de fuentes encontradas por pregunta.

* `hit_at_k` devuelve un booleano: ¿Hay al menos una coincidencia entre los primeros k resultados? `hit_at_k(retrieved, correct, k)  # True o False`
* `recall_at_k` tu función actual cuenta preguntas, no fuentes. Calcula qué proporción de preguntas tiene al menos un **acierto(fuente)**.
* `source_recall_at_k` cuenta **fuentes correctas recuperadas** respecto al total de fuentes correctas, osea de una pregunta devuelve varias fuentes de esa lista el total que sea correcto lo cuenta y lo divide entre el total real y eso se suma al contador y asi para cada uno (preguntas).

### Ejemplos - Varias preguntas
* Imagina que tienes 4 preguntas.

| Pregunta | Fuentes correctas | Recuperadas en top 3 |
|---|---|---|
| P1 | A, B | A, B, X |
| P2 | C, D | C, X, Y |
| P3 | E, F | X, Y, Z |
| P4 | G, H | G, X, Y |

Los resultados serían:
* `hit_at_k` por pregunta: True, True, False, True.
* `recall_at_k`: (3/4 = 0.75), porque 3 de las 4 preguntas tienen al menos un acierto.
* `source_recall_at_k`: (4/8 = 0.5), porque se recuperaron 4 de las 8 fuentes correctas.

### Recall@k
Para cada pregunta, `recall@k` = *(fuentes correctas encontradas en mis primeros k resultados) % (fuentes correctas totales de la pregunta)*.
El `recall` final es la medida de ese valor sobre todas las preguntas respondidas que se incluyen en la evaluación.

* `question_recall_at_k` - Medir una pregunta: ¿qué fracción de sus fuentes encontré?	    - `retrieved`, `correct`, `k`
* `source_recall_at_k` - Recorrer todas las preguntas y hacer la media.	                  - `results`, `dataset`, `k`

**Hipótesis para el tunning.** El IoU entre la unión, así que un chunk grande contra una fuente pequeña de IoU bajo aunque la contenga entera `(p. ej.chunk 0-2000 y fuente 1900-2100 → IoU 0.048 < 0.05, fallo)`. Chunks más pequeños podrían mejorar el recall. A comprobar con `--max_chunk_size`.

#### Tuning 
**Tuning** es ajustar parámetros y pequeñas decisiones de tu sistema, probando una cosa cada vez, para que funcione mejor según una métrica. Aquí la métrica es el `recall@5`. Es como afinar una guitarra: el instrumento ya suena, y giras una clavija, escuchas, y vuelves a ajustar.

**En tu proyecto**
* No es reescribir el programa. Es cambiar valores o pequeñas decisiones y volver a medir:

| Qué se ajusta | Ejemplo |
|---|---|
| Tamaño del chunk | 2000 → 1500 → 1000 → 500 |
| Tokenización | Separar `max_num_seqs` en `max`, `num`, `seqs` |
| Minúsculas y stemming | “running” y “run” cuentan como la misma palabra |
| Solape entre chunks | Que cada chunk repita un 10 % del anterior |

**La regla del tuning** un solo cambio por prueba. Si cambias el tamaño del chunk y la tokenización a la vez y el recall sube, no sabes cuál de las 2 cosas ayudó. Y siempre mides antes y después. Ya tienes tu punto de partida:

| Dataset | recall@5 base |
|---|---:|
| docs | 81.0 % |
| code | 51.5 % |

Caulquier cambio que subas esos números es una mejora. Si baja, lo deshaces. Porque haremos esto ahora porque estamos por encima y justos de los mínimos del subject (80 % y 50 %). Como la evaluación real usa **otras preguntas**, un margen de 1 punto es arriesgado. El tunning sirve para subir ese margen.

## Tamaño de chunk: tope duro incluyendo el solape

**Decisión.** Ningún chunk puede medir más de `max_chunk_size` (2000), solape incluido. En `markdown_chunker.py`, tras calcular el inicio con solape, se limita con `new_start = max(new_start, chunk['end'] - max_chunk_size)`.

**Motivo.** El subject (pág. 11) dice que la moulinette rechaza cualquier fuente de más de 2000 caracteres e invalida todo el output. Antes, el solape de 200 se sumaba al chunk ya cortado a 2000: 86 de 1000 resultados de docs medían hasta 2200.

**Alternativa descartada.** Cortar con presupuesto `max_chunk_size - overlap_size` para que todos los chunks mantengan solape. Más cambios y un caso límite si `max_chunk_size` < solape. Queda como posible experimento de tuning.

**Compromiso.** Los chunks que ya salen llenos (secciones largas troceadas por tamaño) no tienen solape; los demás conservan sus 200.

**Verificación.** Máximo 2000 y 0 resultados >2000 en docs (1000) y code (990). Nueva línea base: docs 51/76/82/90 y code 32.3/46.5/50.5/62.6 (recall@1/3/5/10).