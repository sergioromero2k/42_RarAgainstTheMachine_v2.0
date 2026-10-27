# Experimentos de tuning

Un solo cambio por prueba. Recall@5 en datasets públicos
(docs: 100 preguntas, code: 99). Umbrales del subject: docs 80 %, code 50 %.

| # | Cambio | docs @1/@3/@5/@10 | code @1/@3/@5/@10 | Conclusión |
|---|--------|-------------------|-------------------|------------|
| E0 | Base: chunks ≤ 2000 con solape, tope duro | 51 / 76 / 82 / 90 | 32.3 / 46.5 / 50.5 / 62.6 | Code justo en el límite (50 de 99) |
| E1 | Indexar `file_path + "\n" + texto` del chunk | 56 / 74 / 82 / 90 | 36.4 / 52.5 / 59.6 / 66.7 | Code @5 +9 puntos; docs neutral. Se mantiene |
| E2 | Tokenizador propio: conserva el identificador entero y añade sus partes (`snake_case` y `CamelCase`) | 56 / 74 / 82 / 87 | 46.5 / 65.7 / 73.7 / 81.8 | Code @5 +14; docs neutral (@10 -3). Se mantiene |
| E3 | Stemmer inglés (PyStemmer) sobre todos los tokens, en indexado y consulta | 58 / 76 / 82 / 88 | 43.4 / 68.7 / 75.8 / 84.8 | Mejora pequeña (±1-3 preguntas); docs @5 sin cambios. Se mantiene |
| E5 | Quitar palabras vacías (`bm25s.stopwords.STOPWORDS_EN`, 33 palabras) antes del stemmer | 60 / 76 / 78 / 89 | 44.4 / 72.7 / 82.8 / 84.8 | Code @5 +7 pero docs @5 78 < 80 %. **Descartado** |
| E6a | `b = 0.9` (k1 = 1.5) | 60 / 76 / 79 / 88 | 44.4 / 68.7 / 72.7 / 82.8 | docs @5 79 < 80 %. Descartado |
| E6b | `b = 0.5` (k1 = 1.5) | 55 / 76 / 84 / 88 | 47.5 / 67.7 / 78.8 / 81.8 | @5 +2 docs, +3 code. Prometedor |
| E6c | `b = 0.3` (k1 = 1.5) | 59 / 79 / 81 / 86 | 44.4 / 69.7 / 73.7 / 82.8 | @5 baja en ambos. Óptimo en torno a 0.5 |
| E6 | **Decisión: `b = 0.5`** | 55 / 76 / 84 / 88 | 47.5 / 67.7 / 78.8 / 81.8 | Máximo de @5 en ambos datasets; se mantiene |
| E7a | `k1 = 2.0` (b = 0.5) | 54 / 76 / 83 / 88 | 47.5 / 65.7 / 72.7 / 80.8 | Code @5 -6. Descartado |
| E7b | `k1 = 1.2` (b = 0.5) | 59 / 79 / 84 / 86 | 44.4 / 71.7 / 75.8 / 81.8 | Code @5 -3. Descartado; `k1 = 1.5` se mantiene |