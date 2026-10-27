## Estado a 2026-10-27
Días 1-13 cerrados. Configuración de búsqueda final fijada
(chunks ≤ 2000, tokenizador propio + stemmer, `k1 = 1.5`, `b = 0.5`).
Recall@5: docs 84 %, code 78.8 % (umbrales 80 % y 50 %).

## Pendiente

### Día 15-17 — Generador (siguiente)
- Cargar Qwen3-0.6B con `transformers`.
- Montar el prompt con el contexto recuperado (respetando el límite de tokens).
- `answer` y `answer_dataset` (con `tqdm`, salida `StudentSearchResultsAndAnswer`).

### Día 18-19 — Bonus (opcional)
- Decidir al terminar lo obligatorio. Más baratos: caché y API HTTP local.

### Día 20 — Calidad
- `flake8` y `mypy` con las banderas del subject.
- `models.py:87` (usar `Sequence`), `TypedDict` en los chunkers, tipo de
  `index` en `build_results_index`.
- Docstrings vacíos (`""""""`) en `markdown_chunker.py`.
- `Makefile` (`install`, `run`, `debug`, `clean`, `lint`) y `.gitignore`.
- Tests de casos raros: `k=0`, consulta vacía, fichero inexistente, JSON mal formado.
  Nunca un traceback.
- Valores por defecto de `save_directory` en `answer_dataset`.
- Volver a medir tiempo de indexado (límite 5 min) y de búsqueda
  (límite 90 s para 200 preguntas) con la configuración final.

### Día 21 — Cierre
- `README.md` en inglés con las secciones del subject.
- Prueba de punta a punta desde un clon limpio con `uv sync`.


* Pendiente revisar el chunkers/. cada uno y entnederlo.
* Revisar el indexer.py..