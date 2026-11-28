### Ingestion
---
* `Ingestion`  Es la primera etapa del pipeline. Convierte el repositorio de vLLM en una lista de trozos de texto con su ubicación (archivo y rango de caracteres), lista para indexar. No busca ni puntúa nada. Antes de leer, se asegura de que el repo exista (lo descomprime si hace falta), y si algo está mal, lanza un `RagError` con un mensaje claro.

| Función | Qué hace |
|---|---|
| `__init__(chunkers, raw_data_path)` | Guarda el diccionario extensión → chunker (`.py`, `.md`, `.txt`) y la ruta del repo. No toca disco. |
| `ensure_repo_extracted()` | Si la carpeta del repo no existe, extrae el `.zip` que está a su lado. Lanza `RagError` si no hay ni carpeta ni zip, o si el zip está corrupto. |
| `_read_file(path)` | Lee un archivo como UTF-8. Si no se puede leer, avisa por stderr y devuelve `None` para saltarlo, sin tumbar el indexado. |
| `ingest(max_chunk_size)` | Valida el tamaño (entero ≥ 1, aviso si > 2000), asegura el repo, lista los archivos válidos en orden, los trocea con el chunker de su extensión y devuelve `(MinimalSource, texto)` de cada chunk. Muestra la barra `Chunking`. |

### Tokenizer
---
* `Tokenizer` se encarga de procesar el texto: dividirlo en palabras, separar identificadores compuestos y aplicar stemming. Su objetivo es convertir un texto normal en una lista de palabras procesadas (tokens) para que un buscador pueda trabajar con ellas.

| Elemento | Qué hace |
|---|---|
| `_STEMMER` | Stemmer inglés de PyStemmer, creado **una vez** al importar el módulo para no recrearlo en cada llamada. |
| `tokenize_text(text)` | Convierte un texto en una lista de tokens: extrae palabras de 2 o más caracteres, las pasa a minúsculas, añade también las partes de los identificadores compuestos (`max_num_seqs` y `maxNumSeqs` → `max`, `num`, `seqs`) y aplica stemming. Se usa **igual** al indexar y al buscar. |

### Indexing
---
* `Indexing` = el paso concreto de construir la estructura de búsqueda (BM25).
Estos trabajan juntos para construir un sistema de búsqueda de información basado en BM25.

### Indexer
---
* `indexer` utiliza esos tokens para construir un índice de búsqueda utilizando el algoritmo BM25, guardarlo en disco y recuperarlo posteriormente. BM25 es un algoritmo utilizado en sistemas de recuperación de información (**Information Retrieval**). Su función es calcular qué tan relevante es un documenta para un consulta de búsqueda.

| Elemento | Qué hace |
|---|---|
| `METADATA_FILE` | Nombre del archivo JSON donde se guardan los `MinimalSource` (`sources_metadata.json`). |
| `BM25_K1` y `BM25_B` | Parámetros de BM25: `k1` (cuánto ayuda repetir una palabra) y `b` (cuánto se penalizan los chunks largos). Valores del experimento E6. |
| `__init__(index_path)` | Guarda la ruta del índice y deja vacíos el índice BM25 y la lista de metadatos. |
| `build_index(chunks)` | Recibe `(MinimalSource, texto)`. Rechaza una lista vacía. Concatena `ruta + "\n" + texto` por chunk, guarda los `MinimalSource` en paralelo, tokeniza con barra `Tokenizing` y construye el índice BM25. |
| `save()` | Guarda el índice y los metadatos en `index_path`. Lanza `RagError` si el índice no está construido o no se puede escribir. |
| `load()` | Recupera índice y metadatos del disco. Lanza `RagError` si no existe (*"Run the index command first"*) o está incompleto o corrupto. |

### Evaluator
---
* `evaluator` es un componente que mide si tu sistema RAG funciona correctamente. Comprueba si el buscador recupera los fragmentos de documentos que debería encontrar.
Por ejemplo:
- El buscador encuentra 5 fragmentos.
- El evaluator comprueba cuántos son correctos.
- Calcula métricas como Recall@1, Recall@3, Recall@5 y Recall@10.

| Función | Descripción |
|---|---|
| `is_match()` | Decide si dos fuentes coinciden. |
| `question_recall_at_k()` | Calcula el Recall de una pregunta. |
| `build_results_index()` | Organiza los resultados por pregunta. |
| `source_recall_at_k()` | Calcula el Recall medio de todas las preguntas. |
| `evaluate_files()` | Lee los archivos, ejecuta la evaluación e imprime los resultados. |

### Generator
---
* `generator` es la fase del RAG que utiliza un modelo de inteligencia artificial (en nuestro caso, Qwen3-0.6B) para generar una respuesta a la pregunta del usuario.
Recibe dos cosas:
- La pregunta del usuario.
- El contexto con la información que ha encontrado Retrieval.
Con ambas cosas, el modelo genera una respuesta basada en los documentos recuperados.
Tabla: qué hace cada función

| Función | ¿Qué hace? |
|---|---|
| `read_source_text()` | Lee un fragmento concreto de un archivo. |
| `__init__()` | Carga el modelo Qwen y el tokenizer y configura los límites de tokens. |
| `build_context()` | Junta los fragmentos recuperados por Retrieval en un único contexto, respetando el límite de tokens. |
| `answer()` | Recibe la pregunta y las fuentes, prepara el prompt, se lo pasa a Qwen y devuelve la respuesta generada. |


### Main
---
Es el **punto de entrada** del paquete `src`. Cuando ejecutas `python -m src ...`, Python busca ese arcivo y lo ejecuta. Sin él, `python -m src` daría `error: "No module named src.main"`

Tu proyecto tiene tres capas:
```
terminal  →  __main__.py  →  cli.py (RAGSystem)  →  indexer / retriever / generator...
 (usuario)    (entrada)       (comandos)              (la lógica)
```
* `cli.py` define qué comandos existen (`index`, `search`, `answer`, `evaluate`...).
__main__.py define cómo arranca el programa y qué pasa si algo falla.
El resto hace el trabajo real.


Por ejemplo, imaginemos que tenemos tres documentos:
- Documento 1: contiene información sobre autenticación de usuarios.
- Documento 2: contiene información sobre conexiones a bases de datos.
- Documento 3: contiene información sobre contraseñas.

Si buscamos: `user authentication`
`BM25` calcula qué docuemntos son más relevantes para esa búsqueda.
Para ello tiene en cuenta principalmente:
* 1. Cúantas veces aparece un término en un documento.
* 2. Qué tan frecuente es ese término en toda la colección de documentos.
* 3. La longitud del documento.
Nuestro código utiliza la librería `bm25s` para implementar este algoritmo.

* `retriever` este código implementa un Retriever basados en BM25, cuya función es recuperar los documentos o fragmentos más relevantes para una consulta del usuario. Es una pieza fundamental de un sistema RAG (Retrieval-Augmented Generation), porque se encarga de buscar qué fragmentos de información pueden ayudar a responder una pregunta.

```
data/raw/vllm-0.10.1/   (archivos .py y .md)
        │ trocear
        ▼
   chunks (trozos ≤2000 chars, cada uno con archivo+inicio+fin)
        │ tokenizar
        ▼
   palabras sueltas por chunk
        │ indexar (BM25)
        ▼
   índice → guardado en data/processed/

Pregunta → tokenizar → BM25 puntúa chunks → devuelve los top-k
```

## Chunks
* `BaseChunker`: clase base que define las reglas comunes que deben seguir todos los chunkers.
* `MarkdownChunker`: divide archivos Markdown (.md) respetando, en la medida de lo posible, sus títulos y secciones.
* `PythonChunker`: divide archivos Python (.py) intentando respetar sus funciones y clases.

