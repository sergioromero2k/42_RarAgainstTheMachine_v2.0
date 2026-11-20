* `Ingestion` = Ingestion (ingesta) es la primera fase del pipeline: coger los datos en bruto (los archivos del repositorio de vLLM) y dejarlos preparados para poder buscar en ellos. Es todo lo que ocurre antes de que alguien haga una pregunta, es el proceso completo (leer, trocear, tokenizar, indexar, guardar).
* `Indexing` = el paso concreto de construir la estructura de búsqueda (BM25).

Estos trabajan juntos para construir un sistema de búsqueda de información basado en BM25.
* `Tokenizer` se encarga de procesar el texto: dividirlo en palabras, separar identificadores compuestos y aplicar stemming. Su objetivo es convertir un texto normal en una lista de palabras procesadas (tokens) para que un buscador pueda trabajr con ellas.
* `indexer` utiliza esos tokens para construir un índice de búsqueda utilizando el algoritmo BM25, guardarlo en disco y recuperarlo posteriormente. BM25 es un algoritmo utilizado en sistemas de recuperación de información (**Information Retrieval**).
Su función es calcular qué tan relevante es un documenta para un consulta de búsqueda.

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

