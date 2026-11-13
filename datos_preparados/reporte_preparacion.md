# Etapa 2 — Preparación de datos NASA PROMISE para Machine Learning

**Ejecución (UTC):** 2026-11-13T17:09:27.782156+00:00

**Alcance:** trabajo de preparación y predicción de defectos del Tema 8; se conserva sin cambios el Entregable 1 de Sara.

## Procedimientos aplicados

1. Lectura en modo no destructivo de los cinco CSV originales.
2. Comprobación de SHA-256 contra diagnóstico: obligatoria.
3. Conversión de las 21 métricas a tipos numéricos y estandarización de etiqueta a `defectuoso` (0/1).
4. Eliminación SOLO de filas exactamente idénticas en métricas y etiqueta, manteniendo la primera aparición.
5. Conservación de entradas de métricas idénticas con etiquetas diferentes: no inventamos la etiqueta verdadera.
6. Conservación de valores atípicos: su detección estadística no implica error.
7. Separación de JM1 en entrenamiento y prueba utilizando grupos de métricas iguales para evitar fugas.
8. NO se aplica escalado, normalización por media o imputación global: se hará dentro de los pipelines de entrenamiento, ajustando solo con train.

## Registros después de quitar duplicados exactos

| Dataset | Registros originales | Registros preparados | Duplicados eliminados | Defectuosos preparados | % defectuosos preparados | Grupos contradictorios |
|---|---:|---:|---:|---:|---:|---:|
| CM1 | 498 | 442 | 56 | 48 | 10.86% | 1 |
| JM1 | 13,204 | 8,908 | 4,296 | 2,004 | 22.497% | 88 |
| KC1 | 2,109 | 1,212 | 897 | 315 | 25.99% | 20 |
| KC2 | 522 | 375 | 147 | 105 | 28.0% | 6 |
| PC1 | 1,109 | 954 | 155 | 70 | 7.338% | 6 |

## División de JM1 (dataset candidato inicial)

- Entrenamiento: **7,127 registros**, 22.506% defectuosos.
- Prueba: **1,781 registros**, 22.459% defectuosos.
- Proporción real de prueba: **19.993%**.
- Grupos de métricas compartidos: **0**.

## Decisiones justificadas

- **JM1** se elige como primer candidato por su tamaño. La selección final del dataset/modelo requiere evaluar rendimiento real.
- **No se fusionan** CM1, JM1, KC1, KC2 y PC1: algunas columnas tienen grafías distintas y su equivalencia semántica no se estableció.
- **Desbalance de clases:** la comparación de modelos deberá reportar Recall, Precision, F1 y matriz de confusión; Accuracy sola no basta.
- **Contradicciones:** quedan registradas en archivos de auditoría; un vector con ambas etiquetas no debe ubicarse simultáneamente en train y test.
- **Escalado y datos faltantes:** se hará en etapa de modelado con pipelines, evitando filtraciones del conjunto de prueba.
- **Reproducibilidad:** revisar SHA-256 y `jm1_division.json` antes de integrar.

## Archivos para entregar al siguiente componente

- `*_preparado.csv`: versión limpia por dataset, sin duplicados exactos, con etiqueta binaria.
- `*_auditoria.csv`: fuente, duplicación y contradicciones por fila original.
- `jm1_entrenamiento.csv` y `jm1_prueba.csv`: conjuntos separados para entrenar y evaluar.
- `jm1_mapa_particiones.csv`: mapa de grupos; no es dato de entrada del modelo.
- `jm1_division.json` y `manifiesto_preparacion.json`: decisiones y trazabilidad.

**Aviso:** este reporte describe los resultados de ejecutar el programa con los CSV originales. El archivo `resultados.zip` del diagnóstico, por sí solo, NO contiene todas las filas necesarias para construir estos CSV.
