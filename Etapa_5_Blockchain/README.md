# Etapa 5 — Blockchain académica local (Proyecto IACD)

Componente demostrativo de integridad y trazabilidad SHA-256. **No es una red descentralizada**, no utiliza contratos inteligentes ni impide la reescritura completa por un administrador malicioso. Para detectar una reescritura total se necesitaría conservar una copia verificable del hash final fuera del control de quien administra el archivo.

## Instalación

No tiene dependencias externas. Funciona con Python 3.10+; conserva intacto el trabajo anterior.

Descomprime la carpeta `Etapa_5_Blockchain` dentro de `C:\Users\jesus\OneDrive\Escritorio\Proyecto IACD`, al mismo nivel que `Etapa_3_ML` y `Etapa_4_PNL`.

Desde la raíz `Proyecto IACD`, en PowerShell:

```powershell
python ".\Etapa_5_Blockchain\blockchain.py" registrar --csv ".\Etapa_3_ML\resultados_ml\predicciones_nuevas.csv" --modelo ".\Etapa_3_ML\modelos\modelo_defectos.joblib"
python ".\Etapa_5_Blockchain\blockchain.py" verificar
python ".\Etapa_5_Blockchain\blockchain.py" verificar-fuente --csv ".\Etapa_3_ML\resultados_ml\predicciones_nuevas.csv" --modelo ".\Etapa_3_ML\modelos\modelo_defectos.joblib"
python ".\Etapa_5_Blockchain\blockchain.py" demostrar-alteracion
python -m unittest discover -s ".\Etapa_5_Blockchain\pruebas" -p "probar_*.py" -v
```

**Resultados:** `Etapa_5_Blockchain\datos\cadena.json` contiene la cadena real. La demostración escribe SOLO `Etapa_5_Blockchain\evidencias\cadena_alterada_copia.json`; **nunca cambia** el archivo original ni el CSV de predicciones. Puedes pasar `--cadena "ruta"` para trabajar sobre otra cadena independiente. Registrar por segunda vez agrega un bloque nuevo (no edita el anterior).

## Qué información se registra

Cada bloque almacena índice, fecha UTC, hash anterior, datos, hash de los datos y hash del bloque. Un bloque `lote_predicciones_ml` almacena nombre del CSV (no ruta absoluta), SHA-256 de sus bytes, columnas, número de predicciones, etiquetas y probabilidades no calibradas que figuren en el CSV, número de predicciones positivas, y opcionalmente el SHA-256 del `.joblib` local utilizado.

`verificar` recalcula los hashes internos y detecta alteraciones en los bloques o enlaces. `verificar-fuente` vuelve a calcular el hash de los bytes del CSV (y opcionalmente el del modelo) para detectar cambios **en el archivo original**. `demostrar-alteracion` genera una copia alterada y presenta los errores encontrados.

## Limitaciones y recomendaciones

- Los hashes prueban correspondencia de bytes, no si una predicción es correcta ni si su probabilidad está calibrada.
- La cadena local ofrece detección de ediciones simples y trazabilidad reproducible, no consenso, descentralización ni garantía contra un administrador que reescriba *toda* la cadena. En un sistema real, conservar el hash final fuera del equipo, mediante un tercero o firma, evita esa forma de sustitución.
- La verificación del CSV se hace byte a byte: un cambio de formato o reordenamiento también modifica su hash.
- No hay bloqueo para escritura concurrente; el prototipo está previsto para ejecución local de una sola instancia.
- Los datos de ejemplo provienen de predicciones obtenidas en el proyecto; la ejecución local crea evidencia propia con su archivo actual.
- No registres secretos o información personal en los bloques; no es una base de datos privada.

## Para el dashboard

El backend puede importar funciones de `blockchain_core.py`: `cargar`, `cadena_nueva`, `agregar`, `guardar`, `validar`, `registro_desde_csv`, `comparar_archivo` y `huella_archivo`. Los registros son diccionarios JSON, lo que facilita integrarlos con una API futura. Deben evitar leer/escribir la cadena simultáneamente desde varios procesos.
