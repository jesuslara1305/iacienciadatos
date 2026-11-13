"""Diagnóstico exploratorio de NASA PROMISE (solo lectura sobre CSV originales).

NO limpia, transforma, elimina ni sustituye ningún dato original.
Emite métricas comprobables y salidas en `resultados/`.

Ejecutar:
    python analizar_datasets.py
    python analizar_datasets.py --carpeta-datos "C:/ruta/a/archivos"
"""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Guarda PNG sin exigir interfaz gráfica.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
NOMBRES = ('cm1', 'jm1', 'kc1', 'kc2', 'pc1')
VALORES_NULOS = ['?', 'NA', 'N/A', 'null', 'NULL', 'None', 'none', 'nan', 'NaN', '']
VALORES_ETIQUETA = {
    'true': 1, 'false': 0, 'yes': 1, 'no': 0,
    '1': 1, '0': 0, '1.0': 1, '0.0': 0,
}
FUENTE = 'https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository'


def hash_archivo(ruta: Path) -> str:
    resumen = hashlib.sha256()
    with ruta.open('rb') as archivo:
        for fragmento in iter(lambda: archivo.read(1024 * 1024), b''):
            resumen.update(fragmento)
    return resumen.hexdigest()


def evaluar_archivo(nombre: str, ruta: Path):
    original = pd.read_csv(ruta, keep_default_na=True, na_values=VALORES_NULOS, low_memory=False)
    original.columns = original.columns.str.strip()  # Cambio en memoria; NO en archivo.
    columnas_objetivo = [c for c in original.columns if c.strip().lower() in ('defects', 'problems')]
    if len(columnas_objetivo) != 1:
        raise ValueError(f'{nombre}: se esperaba una sola columna objetivo; encontradas {columnas_objetivo}')
    objetivo = columnas_objetivo[0]
    rasgos = original.drop(columns=[objetivo])

    # Convertir métricas temporalmente solo para diagnosticarlas.
    numericas = rasgos.apply(pd.to_numeric, errors='coerce')
    infinitos = int(np.isinf(numericas.to_numpy(dtype=float)).sum())
    numericas = numericas.replace([np.inf, -np.inf], np.nan)
    erroneos = int((rasgos.notna() & numericas.isna()).sum().sum())

    y_cruda = original[objetivo].astype('string').str.strip().str.lower()
    y = y_cruda.map(VALORES_ETIQUETA)
    invalidas = int((y_cruda.notna() & y.isna()).sum())
    validas = y.dropna().astype(int)
    positivos = int(validas.sum())
    sin_defecto = int((validas == 0).sum())
    conteos_etiquetas = y_cruda.value_counts(dropna=False).to_dict()

    duplicados_totales = int(original.duplicated().sum())
    duplicados_rasgos = int(numericas.duplicated().sum())
    # Duplicidad conflictiva: MISMO vector de rasgos y ambas etiquetas conocidas.
    temp = numericas.copy()
    temp['_etiqueta_diagnostico'] = y
    grupos = temp.dropna(subset=['_etiqueta_diagnostico']).groupby(
        list(numericas.columns), dropna=False, sort=False
    )['_etiqueta_diagnostico']
    grupos_conflictivos = grupos.nunique()
    grupos_conflictivos = grupos_conflictivos[grupos_conflictivos > 1]
    conteo_grupos_conflictivos = int(len(grupos_conflictivos))
    # Conteo de filas de grupos conflictivos, sin sumas cruzadas con NaN de Python.
    filas_conflictivas = 0
    if conteo_grupos_conflictivos:
        ids = pd.util.hash_pandas_object(numericas, index=False)
        for _, indices in temp.groupby(ids, sort=False).groups.items():
            if y.loc[indices].dropna().nunique() > 1:
                filas_conflictivas += len(indices)

    constantes = [c for c in numericas.columns if numericas[c].nunique(dropna=True) <= 1]
    detalles = []
    alertas = []
    for columna in numericas.columns:
        serie = numericas[columna]
        serie_original = rasgos[columna]
        datos_validos = serie.dropna()
        nulos = int(serie.isna().sum())
        fallos_texto = int((serie_original.notna() & serie.isna()).sum())
        valores_negativos = int((serie < 0).sum())
        atipicos = 0
        if len(datos_validos) >= 4:
            q1, q3 = datos_validos.quantile([.25, .75])
            iqr = q3 - q1
            if pd.notna(iqr) and iqr > 0:
                atipicos = int(((serie < q1 - 1.5 * iqr) | (serie > q3 + 1.5 * iqr)).sum())
        detalles.append({
            'dataset': nombre.upper(), 'variable': columna,
            'tipo_leido': str(serie_original.dtype),
            'nulos_y_no_convertibles': nulos, 'porcentaje_nulos': round(nulos * 100 / max(len(original), 1), 3),
            'textos_no_convertibles': fallos_texto,
            'valores_unicos': int(serie.nunique(dropna=True)),
            'minimo': float(datos_validos.min()) if not datos_validos.empty else None,
            'mediana': float(datos_validos.median()) if not datos_validos.empty else None,
            'maximo': float(datos_validos.max()) if not datos_validos.empty else None,
            'valores_negativos': valores_negativos, 'atipicos_IQR_sin_borrar': atipicos,
            'es_constante': columna in constantes,
        })
        if valores_negativos > 0:
            alertas.append(f'{columna}: {valores_negativos} valores negativos (revisar su significado).')
        if fallos_texto > 0:
            alertas.append(f'{columna}: {fallos_texto} valores no convertibles a número.')

    resumen = {
        'dataset': nombre.upper(), 'archivo': ruta.name, 'sha256': hash_archivo(ruta),
        'filas': len(original), 'columnas_totales': len(original.columns),
        'caracteristicas': len(numericas.columns), 'variable_objetivo': objetivo,
        'sin_defecto': sin_defecto, 'con_defecto': positivos,
        'porcentaje_defectuosos': round(100 * positivos / len(validas), 3) if len(validas) else None,
        'etiquetas_nulas': int(y_cruda.isna().sum()), 'etiquetas_no_reconocidas': invalidas,
        'celdas_nulas_entradas': int(rasgos.isna().sum().sum()),
        'celdas_no_convertibles': erroneos,
        'valores_infinitos': infinitos,
        'duplicados_exactos': duplicados_totales,
        'duplicados_entradas': duplicados_rasgos,
        'grupos_entradas_etiquetas_contradictorias': conteo_grupos_conflictivos,
        'filas_en_grupos_contradictorios': filas_conflictivas,
        'columnas_constantes': ', '.join(constantes) if constantes else '',
    }
    if invalidas:
        alertas.append(f'Variable objetivo: {invalidas} etiquetas no reconocidas.')
    if conteo_grupos_conflictivos:
        alertas.append(f'Hay {conteo_grupos_conflictivos} vectores de métricas con etiquetas contradictorias.')
    if duplicados_totales:
        alertas.append(f'Hay {duplicados_totales} filas idénticas (no se eliminan).')
    if infinitos:
        alertas.append(f'Hay {infinitos} valores infinitos en métricas.')

    etiquetas = [
        {'dataset': nombre.upper(), 'valor_original': str(k), 'cantidad': int(v)}
        for k, v in conteos_etiquetas.items()
    ]
    columnas = [{'dataset': nombre.upper(), 'variable': c, 'variable_en_minusculas': c.lower()}
                for c in numericas.columns]
    return resumen, detalles, etiquetas, columnas, alertas


def guardar_graficos(resumen_df: pd.DataFrame, carpeta: Path):
    carpeta.mkdir(parents=True, exist_ok=True)
    if resumen_df.empty:
        return
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(resumen_df['dataset'], resumen_df['filas'])
    ax.set_title('Registros originales por dataset')
    ax.set_ylabel('Número de módulos')
    for i, val in enumerate(resumen_df['filas']):
        ax.text(i, float(val), f'{val:,}', ha='center', va='bottom', fontsize=9)
    fig.tight_layout()
    fig.savefig(carpeta / 'registros_por_dataset.png', dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    izquierda = resumen_df['sin_defecto'].to_numpy()
    ax.bar(resumen_df['dataset'], izquierda, label='Sin defecto')
    ax.bar(resumen_df['dataset'], resumen_df['con_defecto'], bottom=izquierda, label='Con defecto')
    ax.set_title('Distribución de clases (sin limpieza)')
    ax.set_ylabel('Número de módulos')
    ax.legend()
    fig.tight_layout()
    fig.savefig(carpeta / 'distribucion_clases.png', dpi=160)
    plt.close(fig)


def guardar_reporte(resumen: pd.DataFrame, detalles: pd.DataFrame,
                     compat: pd.DataFrame, advertencias: dict, destino: Path):
    lineas = [
        '# Etapa 1 — Diagnóstico exploratorio NASA PROMISE',
        '', f'Generado (UTC): {datetime.now(timezone.utc).isoformat(timespec="seconds")}',
        f'Fuente declarada del repositorio: {FUENTE}',
        '', '> Análisis de solo lectura: no se modificaron, limpiaron, fusionaron ni reemplazaron los CSV originales.',
        '> Los conteos corresponden a estos archivos concretos; conservar el SHA-256 permite verificarlo.',
        '', '## 1. Resumen de los cinco conjuntos', '',
        '| Dataset | Filas | Rasgos | Objetivo | Defectuosos | % defectuosos | Nulos métricas | Duplicados exactos |',
        '|---|---:|---:|---|---:|---:|---:|---:|',
    ]
    for _, r in resumen.iterrows():
        lineas.append(f'| {r.dataset} | {r.filas:,} | {r.caracteristicas} | {r.variable_objetivo} | '
                      f'{r.con_defecto:,} | {r.porcentaje_defectuosos}% | {r.celdas_nulas_entradas:,} | {r.duplicados_exactos:,} |')
    lineas += [
        '', '## 2. Hallazgos y advertencias', '',
        'La variable objetivo se interpreta como 1 = defectuoso, 0 = sin defecto.',
        'Se calculan duplicados de fila completa, duplicados de rasgos y rasgos repetidos con etiquetas contradictorias.',
        'Los valores atípicos IQR son banderas descriptivas y NO implican eliminación automática.',
        'Los valores faltantes, infinitos y métricas no numéricas requieren decisiones justificadas.',
        '',
    ]
    for nombre, alertas in advertencias.items():
        lineas.append(f'### {nombre}')
        lineas.extend([f'- {a}' for a in alertas] if alertas else ['- Sin alertas automáticas.'])
        lineas.append('')
    comunes = compat[compat['presente_en_datasets'] == len(resumen)]['variable_en_minusculas'].tolist()
    lineas.extend([
        '## 3. Compatibilidad entre datasets', '',
        f'Variables con el mismo nombre ignorando mayúsculas en todos los datasets: {len(comunes)}.',
        'No se han fusionado datasets. La coincidencia de nombres NO demuestra equivalencia semántica.',
        'Especial atención: `locCodeAndComment` vs. `lOCodeAndComment`, y diferencias de mayúsculas en PC1.',
        '', '## 4. Propuesta para Machine Learning (no ejecutada todavía)', '',
        '1. Usar JM1 como candidato inicial por su tamaño; no confundir esto con una selección definitiva.',
        '2. Antes de entrenar, validar el tratamiento de faltantes, duplicados y etiquetas con Sara.',
        '3. Mantener la etiqueta fuera de las características y reservar prueba estratificada (p. ej. 20%).',
        '4. Ajustar imputación y escalado SOLO con el subconjunto de entrenamiento usando pipelines.',
        '5. Comparar Regresión Logística, Random Forest y SVM con Precision, Recall, F1 y matriz de confusión.',
        '6. Tratar especialmente el riesgo de fuga si hay filas de entradas repetidas repartidas entre train/test.',
        '7. Guardar resultados y versiones de datos/modelos para la integración con el dashboard.',
        '', '## 5. Archivos generados', '',
        '- `resumen_datasets.csv`: estado general de cada dataset',
        '- `detalle_columnas.csv`: tipos, faltantes, rangos, atípicos y constantes',
        '- `etiquetas_originales.csv`: valores originales y sus frecuencias',
        '- `compatibilidad_columnas.csv`: presencia de variables entre conjuntos',
        '- `graficas/registros_por_dataset.png` y `graficas/distribucion_clases.png`',
        '', '## 6. Nota de coordinación', '',
        'Los resultados de este diagnóstico son exploratorios del Entregable 3 y no sustituyen el Entregable 2 de Sara.',
        'Si Sara produce datasets preparados, deberán evaluarse sus transformaciones antes de entrenar.',
    ])
    destino.write_text('\n'.join(lineas) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Analizar NASA PROMISE sin tocar originales')
    parser.add_argument('--carpeta-datos', type=Path, default=BASE / 'datos_originales',
                        help='Carpeta con cm1.csv, jm1.csv, kc1.csv, kc2.csv y pc1.csv')
    parser.add_argument('--salida', type=Path, default=BASE / 'resultados',
                        help='Carpeta para CSV, informe y gráficas (siempre separada de los originales)')
    args = parser.parse_args()
    datos = args.carpeta_datos.resolve()
    destino = args.salida.resolve()
    if datos == destino or destino in datos.parents or datos in destino.parents:
        # Evitar resultados en el propio directorio con los archivos fuente.
        raise SystemExit('La salida debe estar separada de datos_originales (no debajo de ella).')
    faltantes = [nombre for nombre in NOMBRES if not (datos / f'{nombre}.csv').is_file()]
    if faltantes:
        raise SystemExit('Faltan CSV originales: ' + ', '.join(f'{x}.csv' for x in faltantes)
                         + '\nEjecuta primero: python descargar_datasets.py')
    resumen, detalles, etiquetas, variables, advertencias = [], [], [], [], {}
    for nombre in NOMBRES:
        r, d, e, v, alerts = evaluar_archivo(nombre, datos / f'{nombre}.csv')
        resumen.append(r)
        detalles.extend(d)
        etiquetas.extend(e)
        variables.extend(v)
        advertencias[nombre.upper()] = alerts
        print(f'{nombre.upper():4}  filas={r["filas"]:6,}  entradas={r["caracteristicas"]:2}  '
              f'defectuosos={r["con_defecto"]:5,} ({r["porcentaje_defectuosos"]}%)  '
              f'duplicados={r["duplicados_exactos"]:4}  nulos={r["celdas_nulas_entradas"]:4}')
    resumen_df = pd.DataFrame(resumen)
    detalle_df = pd.DataFrame(detalles)
    etiquetas_df = pd.DataFrame(etiquetas)
    columnas_df = pd.DataFrame(variables)
    compat_df = (columnas_df.groupby('variable_en_minusculas', as_index=False)
                 .agg(presente_en_datasets=('dataset', 'nunique'),
                      datasets=('dataset', lambda x: ', '.join(sorted(set(x)))),
                      nombres_originales=('variable', lambda x: ', '.join(sorted(set(x))))))
    destino.mkdir(parents=True, exist_ok=True)
    resumen_df.to_csv(destino / 'resumen_datasets.csv', index=False, encoding='utf-8-sig')
    detalle_df.to_csv(destino / 'detalle_columnas.csv', index=False, encoding='utf-8-sig')
    etiquetas_df.to_csv(destino / 'etiquetas_originales.csv', index=False, encoding='utf-8-sig')
    compat_df.to_csv(destino / 'compatibilidad_columnas.csv', index=False, encoding='utf-8-sig')
    guardar_graficos(resumen_df, destino / 'graficas')
    guardar_reporte(resumen_df, detalle_df, compat_df, advertencias, destino / 'reporte_diagnostico.md')
    print(f'\nAnálisis concluido. Resultados: {destino}')
    print('Originales conservados. NO se entrenaron modelos ni se aplicaron limpiezas automáticas.')


if __name__ == '__main__':
    main()
