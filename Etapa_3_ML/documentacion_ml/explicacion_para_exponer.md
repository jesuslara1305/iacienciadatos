# Guía para explicar tus entregables ante el profesor

## 1. ¿Qué problema resolvemos?

Queremos estimar si un módulo de software tiene características parecidas a otros módulos que históricamente presentaron defectos. Es una **clasificación supervisada binaria**. Nuestra salida es `0` (sin defecto registrado) o `1` (con defecto registrado). La predicción sirve para priorizar la revisión, **no para afirmar que ya existe un defecto comprobado**.

## 2. ¿Por qué usamos NASA PROMISE?

Es una fuente pública de métricas históricas de módulos. Contamos con CM1, JM1, KC1, KC2 y PC1. En total había **17,442 filas originales**. Después de eliminar solo duplicados exactos quedaron **11,891 filas entre los cinco archivos**. El primer experimento se hizo con JM1 porque es el más grande, con 8,908 filas preparadas.

## 3. ¿Qué hicimos en la Etapa 1?

Aplicamos análisis exploratorio: comprobamos la estructura de los CSV, 21 características por registro, valores faltantes, duplicados, outliers, clases y compatibilidad de columnas. Generamos archivos de diagnóstico y gráficas. No entrenamos modelos en esta etapa.

## 4. ¿Qué hicimos en la Etapa 2?

- Verificamos SHA-256 para asegurar que usábamos los mismos archivos fuente del diagnóstico.
- Convertimos las métricas a números y las etiquetas a `defectuoso` 0/1.
- Borramos solo filas enteras exactamente repetidas. Los vectores con etiquetas contradictorias se conservaron y registraron.
- No eliminamos valores extremos automáticamente porque podrían ser módulos reales grandes o complejos.
- Dividimos JM1 en **7,127** para entrenar y **1,781** para probar.
- Comprobamos **cero grupos de métricas idénticas compartidos** entre ambas particiones.
- Dejamos la estandarización y la imputación en pipelines para evitar calcular parámetros usando test.

## 5. ¿Qué hicimos en la Etapa 3?

Entrenamos Regresión Logística, Random Forest y SVM con parámetros iniciales especificados en el código. Usamos tres pliegues de validación cruzada agrupada para comparar F1 de módulos defectuosos **solo dentro de train**. Regresión Logística tuvo el mejor F1 medio, aunque por poca diferencia frente a SVM, y quedó seleccionada. Después evaluamos los tres en test para documentar sus fortalezas y limitaciones.

## 6. ¿Qué significan las métricas?

- **Accuracy** = (VP + VN) / total. No basta con datos desbalanceados.
- **Precision** = VP / (VP + FP). ¿Cuántas alertas realmente correspondían a defectos?
- **Recall** = VP / (VP + FN). ¿Cuántos defectos reales detectamos?
- **F1** = 2 × Precision × Recall / (Precision + Recall). Compromiso entre ambos.
- **Matriz de confusión**: VP, VN, FP y FN.

En JM1 preparado, 400 de los 1,781 registros de prueba eran defectuosos. **Regresión Logística detectó 201, omitió 199 y tuvo 313 falsas alarmas**. Su Accuracy fue 71.25%, Recall 50.25% y F1 43.98%.

## 7. ¿Por qué no elegimos solo por Accuracy?

Un modelo que predice siempre "sin defecto" consigue un Accuracy de **77.54%** en test, pero Recall y F1 de defectos son **0**: no sirve para priorizar módulos defectuosos. El modelo seleccionado detecta más casos reales a costa de errores y falsas alarmas. Su rendimiento aún debe mejorarse.

## 8. ¿Por qué no usamos los datos de prueba para elegir el modelo?

Porque dejarían de ser una comprobación independiente. La decisión se tomó usando validación cruzada agrupada dentro de los 7,127 registros de entrenamiento. La prueba quedó reservada para la evaluación final.

## 9. ¿Qué guarda el `.joblib`?

Un objeto `Pipeline` de `scikit-learn` que incluye imputación, estandarización (cuando corresponde) y clasificador ya entrenado. Recibe un DataFrame con las **21 columnas de métricas** en el orden establecido en `modelo_metadata.json` y devuelve etiquetas; cuando admite `predict_proba`, devuelve una **probabilidad del modelo no calibrada**, no una estimación confiable de frecuencia real de defectos.

## 10. ¿Cómo integrará Peruano nuestro ML?

El backend deberá enviar las 21 métricas a la función `predecir_dataframe(...)` del módulo `predecir_modulo.py`. El resultado se convertirá a JSON para el dashboard. Esa misma predicción y su metadata podrán enviarse a Blockchain para registrar una huella criptográfica verificable.

## 11. ¿Qué falta del proyecto total?

- **ML:** confirmar ejecución en Windows y guardar captura de terminal; mejoras opcionales solo sobre train, sin reusar test para ajustar.
- **PNL:** elegir una fuente adicional de reportes escritos de defectos; los cinco CSV son datos estructurados y no sustituyen textos.
- **Blockchain:** definir estructura de bloques, hash SHA-256, registro y verificación, detectar alteración.
- **Integración:** acordar con Peruano contrato API/JSON, dashboard y demostración.

## 12. Preguntas probables del profesor

**¿Por qué se usa aprendizaje supervisado?** Porque cada fila histórica incluye una etiqueta conocida de defecto.

**¿Qué es un falso negativo?** Un módulo defectuoso que nuestro modelo clasifica como sin defecto. Aquí fueron 199 para la regresión logística.

**¿Qué son los valores atípicos?** Valores muy alejados del comportamiento común; pueden ser reales, no necesariamente errores.

**¿Por qué usar pesos de clase?** Porque la clase con defectos es minoritaria; esto ayuda a evitar que el algoritmo favorezca exclusivamente la clase mayoritaria.

**¿Cómo evitan fuga de información?** Con una partición fija sin vectores compartidos y pipelines ajustados solo con entrenamiento; la selección usa CV agrupada, no test.

**¿El mejor modelo detecta todos los errores?** No. Detectó aproximadamente la mitad de los casos defectuosos del conjunto de prueba; requiere validación y mejoras futuras.
