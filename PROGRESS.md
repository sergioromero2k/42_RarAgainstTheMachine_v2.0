## Día 12 — Recall alineado con el subject (en curso)

- Leído el subject v2.0. Umbrales confirmados: recall@5 ≥ 80 % docs, ≥ 50 % code.
- Recall redefinido: fracción de fuentes correctas encontradas por pregunta,
  promediada entre preguntas (antes: acierto sí/no).
- `evaluate` ahora usa `--student_search_results_path`, como pide el subject.
- Verificado con datos públicos (docs 54/76/81/89, code 32/46/51/63) y con un caso
  sintético de 2 fuentes.
- Pendiente: tabla de experimentos y primer experimento con `max_chunk_size`.