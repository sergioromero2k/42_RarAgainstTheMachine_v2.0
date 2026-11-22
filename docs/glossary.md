* `Ingestion` = Ingestion (ingesta) es la primera fase del pipeline: coger los datos en bruto (los archivos del repositorio de vLLM) y dejarlos preparados para poder buscar en ellos. Es todo lo que ocurre antes de que alguien haga una pregunta, es el proceso completo (leer, trocear, tokenizar, indexar, guardar).
* `Indexing` = el paso concreto de construir la estructura de búsqueda (BM25).
Estos trabajan juntos para construir un sistema de búsqueda de información basado en BM25.
* `Tokenizer` se encarga de procesar el texto: dividirlo en palabras, separar identificadores compuestos y aplicar stemming. Su objetivo es convertir un texto normal en una lista de palabras procesadas (tokens) para que un buscador pueda trabajar con ellas.
* `indexer` utiliza esos tokens para construir un índice de búsqueda utilizando el algoritmo BM25, guardarlo en disco y recuperarlo posteriormente. BM25 es un algoritmo utilizado en sistemas de recuperación de información (**Information Retrieval**).
Su función es calcular qué tan relevante es un documenta para un consulta de búsqueda.

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

