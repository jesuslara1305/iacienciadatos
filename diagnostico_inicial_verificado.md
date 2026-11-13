# Diagnóstico inicial: revisión directa de los archivos publicados

**Tema 8: Sistema inteligente para el análisis y predicción de defectos en proyectos de software**

**Fuente:** https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository

**Estado:** verificado por consulta de encabezados y cantidad de líneas del repositorio. **Aún no es un perfil estadístico completo**; ese se genera al ejecutar `analizar_datasets.py` con los archivos CSV reales.

| Archivo | Cantidad de registros CSV | Columnas totales | Métricas predictoras | Etiqueta |
|---|---:|---:|---:|---|
| cm1.csv | 498 | 22 | 21 | `defects` (`true/false`) |
| jm1.csv | 13,204 | 22 | 21 | `defects` (`true/false`) |
| kc1.csv | 2,109 | 22 | 21 | `defects` (`true/false`) |
| kc2.csv | 522 | 22 | 21 | `problems` (`yes/no`) |
| pc1.csv | 1,109 | 22 | 21 | `defects` (`true/false`) |

**Observaciones verificadas:**

- JM1 es el único de estos archivos que supera por sí mismo 5,000 registros y es un **candidato inicial**, no la elección definitiva del modelo.
- Las variables son métricas numéricas de software (por ejemplo, `loc`, `v(g)`, `branchCount`, `total_Op`). Son entradas de un modelo de clasificación; no son textos para PNL.
- KC2 tiene diferente nombre y codificación de etiqueta: `problems` con `yes/no`. Esto deberá mapearse de forma consistente si se usa en ML.
- PC1 presenta diferencias en mayúsculas y minúsculas (`v(g)` frente a `V(G)`; `n` frente a `N`), que requieren revisar columnas antes de una eventual integración.
- Aparecen variantes de `locCodeAndComment` / `lOCodeAndComment` según el dataset. No se deben considerar idénticas sin confirmar su definición.

**No se puede afirmar todavía** cuántas filas repetidas, datos faltantes, anomalías o módulos defectuosos hay exactamente en cada archivo sin ejecutar un análisis sobre el contenido íntegro de los CSV. El programa adjunto calcula esas cifras y permite verificarlas.

**Referencias a los archivos originales:**

- https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository/blob/main/cm1.csv
- https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository/blob/main/jm1.csv
- https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository/blob/main/kc1.csv
- https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository/blob/main/kc2.csv
- https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository/blob/main/pc1.csv
