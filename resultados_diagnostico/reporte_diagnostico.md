# Etapa 1 — Diagnóstico exploratorio NASA PROMISE

Generado (UTC): 2026-11-13T16:28:49+00:00
Fuente declarada del repositorio: https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository

> Análisis de solo lectura: no se modificaron, limpiaron, fusionaron ni reemplazaron los CSV originales.
> Los conteos corresponden a estos archivos concretos; conservar el SHA-256 permite verificarlo.

## 1. Resumen de los cinco conjuntos

| Dataset | Filas | Rasgos | Objetivo | Defectuosos | % defectuosos | Nulos métricas | Duplicados exactos |
|---|---:|---:|---|---:|---:|---:|---:|
| CM1 | 498 | 21 | defects | 49 | 9.839% | 0 | 56 |
| JM1 | 13,204 | 21 | defects | 2,103 | 15.927% | 0 | 4,296 |
| KC1 | 2,109 | 21 | defects | 326 | 15.458% | 0 | 897 |
| KC2 | 522 | 21 | problems | 107 | 20.498% | 0 | 147 |
| PC1 | 1,109 | 21 | defects | 77 | 6.943% | 0 | 155 |

## 2. Hallazgos y advertencias

La variable objetivo se interpreta como 1 = defectuoso, 0 = sin defecto.
Se calculan duplicados de fila completa, duplicados de rasgos y rasgos repetidos con etiquetas contradictorias.
Los valores atípicos IQR son banderas descriptivas y NO implican eliminación automática.
Los valores faltantes, infinitos y métricas no numéricas requieren decisiones justificadas.

### CM1
- Hay 1 vectores de métricas con etiquetas contradictorias.
- Hay 56 filas idénticas (no se eliminan).

### JM1
- Hay 88 vectores de métricas con etiquetas contradictorias.
- Hay 4296 filas idénticas (no se eliminan).

### KC1
- Hay 20 vectores de métricas con etiquetas contradictorias.
- Hay 897 filas idénticas (no se eliminan).

### KC2
- Hay 6 vectores de métricas con etiquetas contradictorias.
- Hay 147 filas idénticas (no se eliminan).

### PC1
- Hay 6 vectores de métricas con etiquetas contradictorias.
- Hay 155 filas idénticas (no se eliminan).

## 3. Compatibilidad entre datasets

Variables con el mismo nombre ignorando mayúsculas en todos los datasets: 20.
No se han fusionado datasets. La coincidencia de nombres NO demuestra equivalencia semántica.
Especial atención: `locCodeAndComment` vs. `lOCodeAndComment`, y diferencias de mayúsculas en PC1.

## 4. Propuesta para Machine Learning (no ejecutada todavía)

1. Usar JM1 como candidato inicial por su tamaño; no confundir esto con una selección definitiva.
2. Antes de entrenar, validar el tratamiento de faltantes, duplicados y etiquetas con Sara.
3. Mantener la etiqueta fuera de las características y reservar prueba estratificada (p. ej. 20%).
4. Ajustar imputación y escalado SOLO con el subconjunto de entrenamiento usando pipelines.
5. Comparar Regresión Logística, Random Forest y SVM con Precision, Recall, F1 y matriz de confusión.
6. Tratar especialmente el riesgo de fuga si hay filas de entradas repetidas repartidas entre train/test.
7. Guardar resultados y versiones de datos/modelos para la integración con el dashboard.

## 5. Archivos generados

- `resumen_datasets.csv`: estado general de cada dataset
- `detalle_columnas.csv`: tipos, faltantes, rangos, atípicos y constantes
- `etiquetas_originales.csv`: valores originales y sus frecuencias
- `compatibilidad_columnas.csv`: presencia de variables entre conjuntos
- `graficas/registros_por_dataset.png` y `graficas/distribucion_clases.png`

## 6. Nota de coordinación

Los resultados de este diagnóstico son exploratorios del Entregable 3 y no sustituyen el Entregable 2 de Sara.
Si Sara produce datasets preparados, deberán evaluarse sus transformaciones antes de entrenar.
