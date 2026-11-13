# Etapa 4 — Procesamiento de Lenguaje Natural (PNL)
**Proyecto IACD · Tema 8 · Predicción de defectos en proyectos de software**

## Alcance de este componente
PNL trabaja con **reportes de error escritos**, mientras que el modelo de Machine Learning de la etapa 3 utiliza **21 métricas numéricas** de NASA PROMISE. Son fuentes independientes. No se crea una relación ficticia reporte-módulo. Este componente está preparado para que un dashboard ejecute `analizar_texto.procesar_reporte(...)`.

Implementa cuatro funcionalidades del requisito del profesor:
- **Representación de texto:** limpieza, tokens y matriz TF-IDF (unigramas/bigramas).
- **Análisis de sentimiento:** clasificación técnico-heurística de tono positivo, negativo o neutral con reglas y negaciones simples. *No mide severidad, urgencia, ni riesgo de defectos*.
- **Reconocimiento de entidades:** expresiones regulares y diccionario para SO, tecnología, componentes, versión, códigos de error y archivos. No es NER general de un modelo profundo.
- **Generación de lenguaje:** resúmenes en español mediante plantillas; no usa LLM.

## Requisitos
Python 3.10 o superior y conexión a Internet **solamente para descargar issues reales de GitHub**. Librerías en `requirements.txt`.

## Instalación en Windows (PowerShell)
Abre PowerShell en la raíz de tu proyecto `Proyecto IACD` y ubica `Etapa_4_PNL` directamente dentro de la raíz (no la anides).

```powershell
cd "C:\Users\jesus\OneDrive\Escritorio\Proyecto IACD"
python -m pip install -r ".\Etapa_4_PNL\requirements.txt"
```

## Prueba 1 — Sin Internet (demostración sintética)
El archivo `ejemplos/reportes_sinteticos.csv` tiene 24 reportes **creados solo como simulación**, no son evidencias de incidencias reales. Sus resultados ya se incluyen en `resultados_ejemplo/`.

```powershell
python ".\Etapa_4_PNL\analizar_pnl.py" --entrada ".\Etapa_4_PNL\ejemplos\reportes_sinteticos.csv" --salida ".\Etapa_4_PNL\resultados_ejemplo"
python -m unittest discover -s ".\Etapa_4_PNL\pruebas" -p "probar_*.py" -v
python ".\Etapa_4_PNL\analizar_texto.py" --titulo "Terminal crashes on Windows" --descripcion "Python 3.12 fails with HTTP 500 in app.py"
```

## Prueba 2 — Dataset textual real de GitHub
Recupera issues públicos que tengan la etiqueta **bug** de `microsoft/vscode`, preserva URL de origen, fecha y etiquetas; excluye pull requests. Se recomienda revisar las condiciones de uso y datos potencialmente personales de cada reporte antes de publicarlo. No son datos NASA PROMISE.

```powershell
python ".\Etapa_4_PNL\descargar_reportes.py" --repositorio microsoft/vscode --etiqueta bug --max-reportes 180
python ".\Etapa_4_PNL\analizar_pnl.py"
```

Si el script devuelve errores por API rate limit, espera el restablecimiento o utiliza `GITHUB_TOKEN` (sin escribir el token en el código). Si el repositorio cambia sus etiquetas, usa otra etiqueta válida. No se garantiza un número exacto de registros recuperados. Los resultados se escriben en `Etapa_4_PNL/resultados_reales` y NO se presentan como obtenidos hasta ejecutar dichos comandos.

### Columnas de un CSV propio
Se requieren `titulo,descripcion`; opcionales: `id,source_url,fecha,etiquetas,origen`. Ejemplo: `titulo=Error al iniciar`, `descripcion=La app falla en Windows`, `origen=Propio`.

## Resultados
- `reportes_analizados.csv`: tono, términos relevantes, entidades, resumen por reporte y URL original cuando exista.
- `terminos_tfidf.csv`: relevancia media de términos.
- `entidades_resumen.csv`: categorías y apariciones.
- `ejemplos_analizados.csv`: primeras 10 filas para evidencias.
- `reporte_pnl.json` y `reporte_pnl.md`: informe reproducible y salvedades.
- `distribucion_sentimiento.png`, `terminos_tfidf.png`, `entidades.png`: visualizaciones.

## Archivos
| Archivo | Propósito |
|---|---|
| `descargar_reportes.py` | Obtiene texto real de GitHub REST API (redacción de emails/tokens; no sobrescribe CSV). |
| `pnl_core.py` | Limpieza, tokens, sentimientos heurísticos, entidades y textos de plantilla. |
| `analizar_pnl.py` | Procesa un corpus CSV, calcula TF-IDF y genera resultados. |
| `analizar_texto.py` | Procesa un nuevo reporte individual, integrable en backend. |
| `pruebas/probar_pnl.py` | 8 pruebas sin conexión. |
| `ejemplos/reportes_sinteticos.csv` | 24 ejemplos **simulados** para validar el software. |
| `resultados_ejemplo/` | Evidencia generada sobre los ejemplos simulados, no datos reales. |

## Evidencias para la exposición
1. Terminal de descarga de reportes reales: cantidad, repositorio y API.
2. Cabeceras del CSV real e identificación de `source_url` (sin difundir información sensible).
3. Terminal de `analizar_pnl.py` con cantidad real de reportes.
4. Gráfica de clasificación heurística, términos TF-IDF y entidades del corpus real.
5. Terminal de `analizar_texto.py` mostrando entrada y salida.
6. Ejecución de 8 pruebas con `OK`.

## Alcances y limitaciones
- Un texto con «crash» probablemente recibe tono negativo, pero el tono no indica gravedad.
- Diccionario/reglas pueden producir falsos positivos o no reconocer entidades fuera del vocabulario.
- La elección del corpus por etiqueta y páginas **no es muestreo aleatorio**.
- La API puede fallar por límites, cambios de etiquetas o conexión.
- La API GitHub Issue puede incluir PR; se excluyen explícitamente.
- La disponibilidad pública no implica permiso universal para republicar textos; se prioriza conservación de enlaces de origen.
- No se han realizado pruebas de precisión/recall de PNL con anotaciones humanas sobre un corpus real; no inventar dichos valores.

## Fuentes de metodología y datos
- Especificación original del profesor (`Proyecto Final IA en la Ciencia de Datos.pdf`, sección 7).
- GitHub REST API, list repository issues: https://docs.github.com/en/rest/issues/issues
- Criterio de etiqueta `bug` en VS Code: https://github.com/microsoft/vscode/wiki/Issue-Grooming
