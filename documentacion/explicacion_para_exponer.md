# Explicación de la etapa 1 y la etapa 2 para exposición

## ¿Qué problema estamos resolviendo?
Queremos detectar módulos que podrían presentar defectos mediante patrones aprendidos de métricas históricas del código. Cada registro contiene 21 características y una etiqueta histórica de defectos. No afirmamos detectar defectos directamente desde código fuente ni verificar fallas reales en un programa nuevo.

## Etapa 1: análisis exploratorio de datos

Con un programa Python descargamos y analizamos, **sin modificarlos**, los CSV de NASA PROMISE. Medimos el número de registros, la distribución de módulos defectuosos, la presencia de valores faltantes, registros repetidos, valores atípicos y compatibilidad de columnas. Identificamos 17,442 registros originales en cinco datasets; JM1 tiene 13,204 y es el conjunto inicial por su mayor tamaño.

**Resultados especialmente importantes:** en JM1 hay 4,296 filas exactamente repetidas y 88 grupos de métricas iguales que pueden tener distintas etiquetas. No se reportaron valores faltantes en las métricas. Solo el 15.927% de los registros de JM1 están clasificados como defectuosos, lo que muestra desbalance de clases.

**No entrenamos modelos en esta etapa.** El análisis responde a la pregunta «¿qué datos tengo y qué problemas presentan?».

## Etapa 2: preparación para Machine Learning

1. Validamos que los archivos originales coincidan con los analizados, mediante SHA-256.
2. Estandarizamos el indicador de defecto a 0 (sin defecto) y 1 (con defecto).
3. Convertimos las métricas numéricas de forma consistente.
4. Quitamos **únicamente** las filas exactamente duplicadas. Las métricas iguales con etiquetas distintas se conservan y documentan porque no conocemos cuál etiqueta es correcta.
5. No quitamos automáticamente valores atípicos: una complejidad o tamaño altos pueden ser reales.
6. Elegimos JM1 como primer conjunto de trabajo, sin combinar todavía proyectos distintos.
7. Reservamos datos de prueba en grupos de características que no coinciden con los utilizados para entrenar.
8. Dejamos pendiente el escalado y, si hiciera falta, la imputación, para hacerlos con pipelines ajustados **solo dentro de los datos de entrenamiento**.

**¿Por qué esta preparación es necesaria?** Para reducir problemas de calidad, impedir fugas de información entre entrenamiento y prueba y obtener una evaluación posterior más realista.

## Respuestas útiles durante la presentación

**¿Por qué JM1 y no los demás?** Es el más grande de los cinco, supera la referencia de 5,000 registros y permite empezar con suficientes ejemplos. Los demás podrán utilizarse en análisis complementarios; no se suman por simple coincidencia de nombres de columnas.

**¿Qué son métricas de software?** Mediciones del código fuente, como líneas de código, complejidad y cantidad de operadores, que pueden relacionarse estadísticamente con la existencia de defectos.

**¿Qué significa que el dataset esté desbalanceado?** Hay muchos más módulos sin defectos que con defectos. Un modelo podría tener alta exactitud prediciendo siempre la clase dominante y aun así fallar en la detección de defectos. Por ello utilizaremos Recall, F1 y matriz de confusión además de Accuracy.

**¿Por qué no eliminar todos los valores atípicos?** Porque no todos son errores de captura; valores grandes de tamaño o complejidad pueden corresponder a módulos reales.

**¿Cómo prevenimos fugas de información?** Separando conjuntos antes de ajustar transformaciones y garantizando que vectores idénticos de métricas no queden repartidos en entrenamiento y prueba.

**¿Qué queda pendiente?** Ejecutar el código de preparación con los cinco CSV originales, inspeccionar el reporte resultante y entrenar y evaluar los algoritmos de clasificación.
