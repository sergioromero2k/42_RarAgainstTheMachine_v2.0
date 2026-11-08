* `Ingestion` = Ingestion (ingesta) es la primera fase del pipeline: coger los datos en bruto (los archivos del repositorio de vLLM) y dejarlos preparados para poder buscar en ellos. Es todo lo que ocurre antes de que alguien haga una pregunta, es el proceso completo (leer, trocear, tokenizar, indexar, guardar).
* `Indexing` = el paso concreto de construir la estructura de búsqueda (BM25).


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

