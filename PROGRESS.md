## Pendiente

### Día 15-16 (generador): casi cerrado
- [ ] Medir dónde se va el tiempo (prefill vs. generación). Ahora: ~110 s por pregunta, con 3000 tokens de contexto, k=5 y 200 tokens nuevos
- [ ] Probar, de uno en uno, MAX_CONTEXT_TOKENS 1500, k=3 y MAX_NEW_TOKENS 100, comprobando que la calidad no baja
- [ ] Ejecutar `answer_dataset` sobre docs y code, con save_directory separado por dataset
- [ ] Mirar en el subject cómo se evalúa la calidad de la respuesta generada

### Día 17: prompt
- [ ] Afinar el prompt: respuesta fundamentada en el contexto, concisa, y "no lo sé" si no está

### Días 18-19: bonus (opcional)
- [ ] Decidir si hago alguno (los más baratos: caching o API HTTP local)

### Día 20: calidad
- [ ] flake8 y mypy con los flags del subject
- [ ] Makefile (install, run, debug, clean, lint) y `.gitignore`
- [ ] Casos límite sin traceback: k=0, query vacía, fichero inexistente, JSON mal formado
- [ ] `encoding="utf-8"` en ingestion y en `read_source_text`
- [ ] Rellenar docstrings vacíos y entradas pendientes de DECISIONS (tokenizer, BM25)
- [ ] Volver a medir tiempo de indexado (<5 min) y de búsqueda (<90 s por 200 preguntas)

### Día 21: entrega
- [ ] README en inglés con las secciones obligatorias
- [ ] Prueba completa desde un clone limpio con `uv sync`