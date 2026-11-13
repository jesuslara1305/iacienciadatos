# Etapa 3 — Machine Learning, Tema 8 NASA PROMISE

## Cómo integrarlo en `Proyecto IACD` (Windows)

1. **Conserva** tus carpetas `datos_originales/`, `datos_preparados/`, `resultados/`, `documentacion/` y todos los scripts previos tal como están.
2. Descomprime el ZIP **dentro de `C:\Users\jesus\OneDrive\Escritorio\Proyecto IACD`** para que quede una carpeta nueva llamada `Etapa_3_ML`, al mismo nivel que `datos_preparados`. No copies ni reemplaces archivos de la etapa 2 o de Sara.
3. Abre PowerShell en la carpeta `Proyecto IACD` y ejecuta:

```powershell
python -m pip install -r Etapa_3_ML\requirements.txt
python Etapa_3_ML\entrenar_modelos.py
python Etapa_3_ML\pruebas_ml.py
python Etapa_3_ML\predecir_modulo.py --archivo Etapa_3_ML\ejemplos\ejemplo_nuevos_modulos.csv
```

El segundo comando **repite todo el entrenamiento y genera las evidencias en tu computadora**; también recrea los modelos en `Etapa_3_ML\modelos`. El último hace cinco predicciones de demostración. Si deseas indicar explícitamente la carpeta de datos:

```powershell
python Etapa_3_ML\entrenar_modelos.py --carpeta-datos "C:\Users\jesus\OneDrive\Escritorio\Proyecto IACD\datos_preparados"
```

## Qué contiene el paquete

- `entrenar_modelos.py`: validaciones de entrada, selección de modelo por validación cruzada agrupada **solo en train**, entrenamiento de Regresión Logística/Random Forest/SVM y evaluación final en test.
- `predecir_modulo.py`: predicciones nuevas, exportables a CSV e integrables en el backend.
- `modelos/modelo_defectos.joblib`: modelo final con preprocesamiento integrado (ajustar en tu entorno si hay diferencias de versión de scikit-learn).
- `modelos/modelo_metadata.json`: columnas, criterio, versiones y SHA-256 de los archivos preparados.
- `resultados_ml/comparacion_validacion_cruzada.csv`, `comparacion_prueba.csv`, `predicciones_jm1_prueba.csv` y gráficas: evidencias reales de entrenamiento y prueba.
- `documentacion_ml/informe_resultados_ml.md`: redacción técnica del entregable 3.
- `ejemplos/ejemplo_nuevos_modulos.csv`: cinco registros para demostrar el uso de la función predictiva, sin la etiqueta real.

## Restricciones científicas

- La **selección de modelo es por F1 promedio en validación cruzada de entrenamiento**; no se selecciona por test.
- Se preserva la clase positiva `defectuoso=1` en Precision/Recall/F1.
- Los vectores de métricas duplicados (incluso con distinta etiqueta) permanecen agrupados.
- La mediana y la escala se ajustan dentro de cada fold de entrenamiento.
- Se conserva la división original 7127/1781 de la Etapa 2, sin barajar o volver a dividir JM1.
- Un SVM sin calibración produce **puntaje de decisión**, no probabilidad.
- La evaluación de JM1 no prueba generalización a todos los proyectos.

## Compatibilidad del modelo serializado

Los modelos `.joblib` pueden requerir **la misma versión de scikit-learn** empleada al crearlos, indicada en `modelos/modelo_metadata.json`. La manera más confiable de generar los modelos para tu equipo es ejecutar `python entrenar_modelos.py` localmente. **Nunca cargues `.joblib` de fuentes desconocidas**, ya que deserializar archivos pickle puede ejecutar código.

## Integración con Peruano (Dashboard)

Desde el backend Python se puede usar:

```python
import pandas as pd
from Etapa_3_ML.predecir_modulo import predecir_dataframe

nuevo = pd.read_csv('Etapa_3_ML/ejemplos/ejemplo_nuevos_modulos.csv')
resultado, metadata = predecir_dataframe(nuevo)
print(resultado)
```

El backend puede convertir `resultado` a JSON para visualizar la predicción, el puntaje o probabilidad no calibrada (cuando existe) y enviarla después al componente Blockchain. Deben definir juntos el contrato final de integración.

**Importante:** los números de `predict_proba` se guardan como `probabilidad_defecto_no_calibrada`. Con clases desbalanceadas y `class_weight`, no deben interpretarse como porcentajes reales de ocurrencia sin calibración aparte.
