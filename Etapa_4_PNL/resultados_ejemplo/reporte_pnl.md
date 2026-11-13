# Informe de resultados PNL

**AVISO: ESTA EJECUCIÓN UTILIZA EJEMPLOS SINTÉTICOS, NO SON REPORTES REALES.**

Se analizaron 24 reportes (dataset proporcionado / ejemplos). La clasificación heurística del tono fue: negativo 10, neutral 7 y positivo 7. Los términos TF-IDF destacados fueron: python, editor, issue, extension, error. Las categorías de entidades más frecuentes: COMPONENTE (25), TECNOLOGIA (12), VERSION (9). Estas estadísticas describen el texto; no son predicciones de defectos NASA ni medidas de severidad.

## Metodología

1. Limpieza y tokenización.
2. Representación TF-IDF.
3. Polaridad de expresiones por reglas.
4. Reconocimiento de entidades por patrones.
5. Generación de resúmenes mediante plantillas.

## Limitaciones

- Tono no equivale a severidad
- Heurísticas no validadas con etiquetas humanas
- NER depende de patrones conocidos
- Reportes de GitHub no tienen correspondencia individual con métricas de NASA PROMISE
- Muestra de issues no necesariamente representativa
