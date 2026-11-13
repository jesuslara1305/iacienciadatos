# Interpretación del ZIP «resultados.zip» aportado por el equipo

Se recibieron `resumen_datasets.csv`, `detalle_columnas.csv`, `etiquetas_originales.csv`, `compatibilidad_columnas.csv`, dos gráficas PNG y `reporte_diagnostico.md`. **Este ZIP no contiene los CSV originales ni registros fila a fila.**

| Dataset | Originales | Filas exactas duplicadas detectadas | Filas que quedarán SI solo se quitan esas repeticiones | % defectuosos originales |
|---|---:|---:|---:|---:|
| CM1 | 498 | 56 | 442 | 9.839% |
| JM1 | 13,204 | 4,296 | 8,908 | 15.927% |
| KC1 | 2,109 | 897 | 1,212 | 15.458% |
| KC2 | 522 | 147 | 375 | 20.498% |
| PC1 | 1,109 | 155 | 954 | 6.943% |
| **Total** | **17,442** | **5,551** | **11,891** | — |

Los conteos «filas que quedarán» son **deducciones aritméticas del diagnóstico**: `originales - duplicados_exactos`. No representan un procesamiento nuevo de los CSV que todavía no se proporcionaron en este turno. La ejecución del script es necesaria para producir y verificar los archivos de salida reales; si la conversión de valores hace coincidir filas adicionales se reportará en el nuevo manifiesto.

El diagnóstico informa **cero celdas nulas, valores infinitos y métricas no convertibles** en los cinco archivos, además de:

| Dataset | Grupos de métricas con etiquetas contradictorias | Filas originales dentro de esos grupos |
|---|---:|---:|
| CM1 | 1 | 2 |
| JM1 | 88 | 1,116 |
| KC1 | 20 | 253 |
| KC2 | 6 | 118 |
| PC1 | 6 | 13 |

Estos grupos son **distintos de los duplicados exactos**. No se deben borrar ni resolver por mayoría sin justificarlo. Para el ensayo inicial de JM1 se conservarán y se separarán por grupos al crear la partición de prueba.

**Responsabilidades confirmadas:** Sara elaboró el análisis del problema (Entregable 1). La preparación de datos y el modelo de Machine Learning son responsabilidad del estudiante encargado de los entregables 3, 4 y 5. No se alteran los documentos de Sara.
