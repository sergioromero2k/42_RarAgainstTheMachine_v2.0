# Experimentos de tuning

Un solo cambio por prueba. Recall@5 en datasets públicos
(docs: 100 preguntas, code: 99). Umbrales del subject: docs 80 %, code 50 %.

| # | Cambio | docs @1/@3/@5/@10 | code @1/@3/@5/@10 | Conclusión |
|---|--------|-------------------|-------------------|------------|
| E0 | Base: chunks ≤ 2000 con solape, tope duro | 51 / 76 / 82 / 90 | 32.3 / 46.5 / 50.5 / 62.6 | Code justo en el límite (50 de 99) |
| E1 | Indexar `file_path + "\n" + texto` del chunk | 56 / 74 / 82 / 90 | 36.4 / 52.5 / 59.6 / 66.7 | Code @5 +9 puntos; docs neutral. Se mantiene |
| E3 | Stemmer inglés (PyStemmer) sobre todos los tokens, en indexado y consulta | 58 / 76 / 82 / 88 | 43.4 / 68.7 / 75.8 / 84.8 | Mejora pequeña (±1-3 preguntas); docs @5 sin cambios. Se mantiene |