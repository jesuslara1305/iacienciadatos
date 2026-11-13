# Entregable 3 — Entrenamiento y evaluación de Machine Learning

## Objetivo
Clasificar módulos de software en **sin defectos (0)** y **con defectos (1)**, utilizando 21 métricas históricas del dataset JM1 de NASA PROMISE.

## Preparación
Los duplicados exactos se quitaron en etapa 2; se conservaron vectores con etiquetas contradictorias y valores atípicos. Se utilizó una división fija de 7,127 filas para entrenar y 1,781 para probar. El mismo vector de métricas nunca se comparte entre ambos conjuntos.

## Algoritmos
Se usaron Regresión Logística, Random Forest y SVM con kernel RBF. La regresión y SVM escalan las métricas; Random Forest no requiere escalado. Los pipelines imputan mediana y, cuando procede, estandarizan utilizando solo las filas de entrenamiento de cada fold. Se utilizaron pesos de clase balanceados por el desbalance de etiquetas.

## Selección sin fuga
La selección del modelo se efectuó únicamente con validación cruzada de 3 particiones agrupadas por identidad del vector de métricas. No se ajustaron modelos, hiperparámetros ni umbrales mirando el conjunto de prueba. Las configuraciones son iniciales, no el resultado de una búsqueda exhaustiva de hiperparámetros.

## Resultados de validación cruzada (solo entrenamiento)

| Algoritmo | F1 medio | Recall medio | Precision media | Accuracy media |
|---|---:|---:|---:|---:|
| Regresion logistica | 0.4423 | 0.5137 | 0.3883 | 0.7084 |
| SVM (RBF) | 0.4412 | 0.5480 | 0.3699 | 0.6874 |
| Random Forest | 0.4150 | 0.3691 | 0.4745 | 0.7660 |

**Modelo seleccionado por validación cruzada:** Regresion logistica.

## Resultados en test fijo (1,781 registros)

| Modelo | Accuracy | Precision | Recall | F1 | TN | FP | FN | TP | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Regresion logistica | 0.7125 | 0.3911 | 0.5025 | 0.4398 | 1068 | 313 | 199 | 201 | 0.7015 |
| Random Forest | 0.7563 | 0.4514 | 0.3950 | 0.4213 | 1189 | 192 | 242 | 158 | 0.6975 |
| SVM (RBF) | 0.6727 | 0.3527 | 0.5475 | 0.4290 | 979 | 402 | 181 | 219 | 0.6959 |

**Línea base (siempre clase mayoritaria):** Accuracy 0.7754; Recall 0.0000; F1 0.0000.

## Interpretación de métricas
- **Accuracy:** proporción total de aciertos; puede ser engañosa en clases desbalanceadas.
- **Precision:** entre módulos señalados como defectuosos, proporción realmente defectuosa.
- **Recall:** de todos los módulos defectuosos reales, proporción detectada.
- **F1:** media armónica de precision y recall de la clase positiva.
- **TN, FP, FN, TP:** verdaderos negativos, falsos positivos, falsos negativos y verdaderos positivos.
- **ROC AUC:** separación entre clases sin depender del umbral de clasificación.

## Archivos generados
- `modelos/modelo_defectos.joblib`: pipeline seleccionado con preprocesamiento integrado.
- `modelos/modelo_*`: los tres pipelines entrenados.
- `modelos/modelo_metadata.json`: columnas, decisiones, versiones, hashes de origen.
- `resultados_ml/comparacion_validacion_cruzada.csv`: métricas usadas para seleccionar.
- `resultados_ml/comparacion_prueba.csv`: evaluación final de los tres.
- `resultados_ml/predicciones_jm1_prueba.csv`: predicciones auditables.
- `resultados_ml/*.png`: matrices y curvas.

## Limitaciones
1. Los datos NASA PROMISE son históricos y su distribución puede diferir de proyectos actuales.
2. JM1 incluye métricas iguales con etiquetas diferentes: existe ruido o ambigüedad en esas observaciones.
3. El riesgo estimado no prueba que existan defectos; es un apoyo a la priorización de pruebas.
4. La evaluación se realizó dentro de JM1; no demuestra generalización a otros proyectos.
5. La probabilidad de Regresión Logística o Random Forest NO ha sido calibrada; SVM ofrece un puntaje de decisión, no una probabilidad.
6. Se usaron configuraciones iniciales; una optimización de hiperparámetros debe ocurrir solo dentro de entrenamiento.

## Evidencia de ejecución
Modelos serializados, predicciones CSV y gráficas construidas a partir del split real de JM1; la tabla de arriba proviene de la ejecución del código. Conservar una captura de la terminal de ejecución local.
