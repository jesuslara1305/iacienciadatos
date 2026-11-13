"""Preparación reproducible de NASA PROMISE para clasificación de defectos.

Lee cm1.csv, jm1.csv, kc1.csv, kc2.csv y pc1.csv sin modificarlos.
Genera copias numéricas con etiqueta binaria; elimina solamente duplicados
EXACTOS (mismas métricas y etiqueta), mantiene grupos de métricas con
etiquetas contradictorias y produce un test de JM1 SIN fuga entre grupos.

Ejemplos:
  python preparar_datos.py
  python preparar_datos.py --carpeta-datos "C:/datasets/NASA"
  python preparar_datos.py --sin-verificar-hash
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

RAIZ = Path(__file__).resolve().parent
DATASETS = ('cm1', 'jm1', 'kc1', 'kc2', 'pc1')
ETIQUETAS = {'true': 1, 'false': 0, 'yes': 1, 'no': 0,
             '1': 1, '0': 0, '1.0': 1, '0.0': 0}
OBJETIVOS = {'defects', 'problems'}
NULLS = ['?', 'NA', 'N/A', 'null', 'NULL', 'None', 'none', 'nan', 'NaN', '']


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with ruta.open('rb') as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()


def guardar_json(ruta: Path, datos: dict) -> None:
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def validar_rutas(entrada: Path, salida: Path) -> None:
    if entrada == salida or entrada in salida.parents or salida in entrada.parents:
        raise ValueError('La salida debe ser independiente de la carpeta de datos originales.')


def cargar_diagnostico(carpeta: Path) -> dict:
    ruta = carpeta / 'resumen_datasets.csv'
    if not ruta.exists():
        raise FileNotFoundError(f'Falta {ruta}; se usa para verificar los archivos del diagnóstico enviado.')
    diag = pd.read_csv(ruta)
    requeridas = {'dataset', 'archivo', 'sha256', 'filas', 'duplicados_exactos'}
    if not requeridas.issubset(diag.columns):
        raise ValueError(f'Diagnóstico incompleto; faltan: {sorted(requeridas - set(diag.columns))}')
    return {str(r.dataset).lower(): r for r in diag.itertuples(index=False)}


def cargar_y_normalizar(nombre: str, ruta: Path) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    original = pd.read_csv(ruta, keep_default_na=True, na_values=NULLS, low_memory=False)
    original.columns = [str(c).strip() for c in original.columns]
    if len(set(original.columns)) != len(original.columns):
        raise ValueError(f'{nombre}: nombres de columnas duplicados después de quitar espacios.')
    objetivos = [c for c in original.columns if c.lower() in OBJETIVOS]
    if len(objetivos) != 1:
        raise ValueError(f'{nombre}: se esperaba una única etiqueta defects/problems; hay {objetivos}.')
    objetivo = objetivos[0]
    entradas = original.drop(columns=objetivo)
    if len(entradas.columns) != 21:
        raise ValueError(f'{nombre}: se esperaban 21 métricas; se detectaron {len(entradas.columns)}.')
    X = entradas.apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], np.nan)
    no_numericos = (entradas.notna() & X.isna()).sum()
    if no_numericos.sum():
        raise ValueError(f'{nombre}: hay datos no numéricos que requieren revisión: '
                         f'{no_numericos[no_numericos > 0].to_dict()}')
    if X.isna().any().any():
        print(f'AVISO {nombre.upper()}: se preservan valores faltantes; imputar SOLO en entrenamiento.')
    crudo = original[objetivo].astype('string').str.strip().str.lower()
    y = crudo.map(ETIQUETAS)
    if y.isna().any():
        frecuencia = crudo[y.isna()].value_counts(dropna=False).to_dict()
        raise ValueError(f'{nombre}: etiquetas sin interpretar: {frecuencia}. No se descartan registros.')
    if not set(y.unique()).issubset({0, 1}):
        raise ValueError(f'{nombre}: etiqueta objetivo no binaria.')
    normal = X.copy()
    normal['defectuoso'] = y.astype('int8')
    return original, normal, objetivo


def preparar_un_dataset(nombre: str, ruta: Path, destino: Path, esperado, validar_hash: bool):
    checksum = sha256(ruta)
    if validar_hash and checksum.lower() != str(esperado.sha256).lower():
        raise ValueError(f'{nombre}: SHA-256 distinto al del diagnóstico recibido.\n'
                         f'  Actual: {checksum}\n  Diagnóstico: {esperado.sha256}\n'
                         'Revisa que el CSV sea el mismo; si cambió de versión, genera un nuevo diagnóstico. '
                         'Para correr de todos modos: --sin-verificar-hash (quedará anotado).')
    original, normal, etiqueta_origen = cargar_y_normalizar(nombre, ruta)
    if len(normal) != int(esperado.filas):
        raise ValueError(f'{nombre}: cantidad de registros diferente del diagnóstico.')

    # Eliminar repetición estricta de la fila completa; no elegir etiquetas por mayoría.
    duplicados = normal.duplicated(keep='first')
    sin_duplicados = normal.loc[~duplicados].copy()
    entradas_limpias = sin_duplicados.drop(columns=['defectuoso'])
    grupos = pd.util.hash_pandas_object(entradas_limpias, index=False).astype(str)
    grupos_nunicas = (sin_duplicados.assign(_grupo=grupos)
                      .groupby('_grupo')['defectuoso'].nunique())
    conflictivos = set(grupos_nunicas[grupos_nunicas > 1].index)

    salida_csv = destino / f'{nombre}_preparado.csv'
    sin_duplicados.to_csv(salida_csv, index=False, float_format='%.17g')

    audit = pd.DataFrame({
        'fila_csv_original': np.arange(2, len(normal) + 2, dtype=int),
        'etiqueta_normalizada': normal['defectuoso'].to_numpy(),
        'duplicado_exacto_eliminado': duplicados.to_numpy(),
    })
    # La huella es únicamente para trazabilidad; NO una variable del modelo.
    huellas_originales = pd.util.hash_pandas_object(normal.drop(columns='defectuoso'), index=False).astype(str)
    audit['grupo_de_metricas'] = huellas_originales.to_numpy()
    audit['grupo_con_etiquetas_contradictorias'] = audit['grupo_de_metricas'].isin(conflictivos)
    audit.to_csv(destino / f'{nombre}_auditoria.csv', index=False)

    estadisticas = {
        'dataset': nombre.upper(),
        'objetivo_origen': etiqueta_origen,
        'objetivo_preparado': 'defectuoso',
        'columnas_metricas': entradas_limpias.columns.tolist(),
        'filas_originales': int(len(original)),
        'filas_preparadas': int(len(sin_duplicados)),
        'duplicados_exactos_eliminados': int(duplicados.sum()),
        'defectuosos_originales': int(normal['defectuoso'].sum()),
        'defectuosos_preparados': int(sin_duplicados['defectuoso'].sum()),
        'porcentaje_defectuosos_preparados': round(float(sin_duplicados['defectuoso'].mean()*100), 3),
        'grupos_metricas_con_etiquetas_contradictorias': int(len(conflictivos)),
        'filas_preparadas_en_grupos_contradictorios': int(grupos.isin(conflictivos).sum()),
        'celdas_faltantes_preparadas': int(entradas_limpias.isna().sum().sum()),
        'filas_con_metricas_iguales_y_distinta_etiqueta_conservadas': True,
        'valores_atipicos_eliminados': 0,
        'sha256_original': checksum,
        'sha256_preparado': sha256(salida_csv),
        'hash_original_coincide_diagnostico': checksum.lower() == str(esperado.sha256).lower(),
    }
    return sin_duplicados.reset_index(drop=True), estadisticas


def dividir_jm1(datos: pd.DataFrame, destino: Path) -> dict:
    entradas = datos.drop(columns=['defectuoso'])
    y = datos['defectuoso'].to_numpy(dtype=int)
    grupos = pd.util.hash_pandas_object(entradas, index=False).astype(str).to_numpy()
    objetivo_fraction = 0.20
    tasa_positivos = float(y.mean())
    best = None
    # Se elige solamente por tamaño / balance de clases; NUNCA se miran resultados del modelo.
    cortes = GroupShuffleSplit(n_splits=120, test_size=objetivo_fraction, random_state=42)
    for train_idx, test_idx in cortes.split(entradas, y, groups=grupos):
        y_train, y_test = y[train_idx], y[test_idx]
        if len(set(y_train)) != 2 or len(set(y_test)) != 2:
            continue
        propor = len(test_idx) / len(datos)
        tasa_test, tasa_train = float(y_test.mean()), float(y_train.mean())
        score = 3*abs(propor-objetivo_fraction) + 2*abs(tasa_test-tasa_positivos) + abs(tasa_train-tasa_positivos)
        if best is None or score < best[0]:
            best = (score, train_idx, test_idx)
    if best is None:
        raise ValueError('No se consiguió una división con ambas clases en train y test.')
    _, i_ent, i_prue = best
    ent, prue = datos.iloc[i_ent].copy(), datos.iloc[i_prue].copy()
    grupos_ent, grupos_prue = set(grupos[i_ent]), set(grupos[i_prue])
    if grupos_ent.intersection(grupos_prue):
        raise AssertionError('Fuga entre conjuntos: grupos de métricas repetidos.')
    if len(ent) + len(prue) != len(datos):
        raise AssertionError('Las particiones no cubren el total de datos.')
    columnas = list(datos.columns)
    assert set(columnas) == set(ent.columns) == set(prue.columns)
    ent.to_csv(destino / 'jm1_entrenamiento.csv', index=False, float_format='%.17g')
    prue.to_csv(destino / 'jm1_prueba.csv', index=False, float_format='%.17g')
    # Índice de origen EN EL CSV PREPARADO (fila 2 = primer registro) para auditar el split.
    pd.DataFrame({'fila_csv_preparado': np.arange(2,len(datos)+2),
                  'grupo_de_metricas': grupos,
                  'particion': np.where(np.isin(np.arange(len(datos)), i_ent), 'entrenamiento', 'prueba')
                  }).to_csv(destino / 'jm1_mapa_particiones.csv', index=False)
    info = {
        'dataset': 'JM1', 'semilla': 42,
        'metodo': 'GroupShuffleSplit; 120 candidatos, selección determinista por proporción y balance (no por rendimiento)',
        'objetivo_porcentaje_prueba': 20,
        'filas_preparadas': len(datos),
        'filas_entrenamiento': len(ent),
        'filas_prueba': len(prue),
        'porcentaje_prueba_real': round(100*len(prue)/len(datos), 3),
        'positivos_entrenamiento': int(ent.defectuoso.sum()),
        'positivos_prueba': int(prue.defectuoso.sum()),
        'tasa_defectos_entrenamiento': round(100*float(ent.defectuoso.mean()), 3),
        'tasa_defectos_prueba': round(100*float(prue.defectuoso.mean()), 3),
        'grupos_de_metricas_compartidos': len(grupos_ent & grupos_prue),
        'variable_objetivo': 'defectuoso',
        'columnas_entradas': [c for c in columnas if c!='defectuoso'],
        'advertencia': 'No entrenar, escalar, imputar ni ajustar hiperparámetros con jm1_prueba.csv.',
    }
    guardar_json(destino/'jm1_division.json',info)
    return info


def generar_reporte(ruta: Path, manifest: list[dict], split: dict, verificar_hash: bool) -> None:
    l = [
        '# Etapa 2 — Preparación de datos NASA PROMISE para Machine Learning', '',
        f'**Ejecución (UTC):** {datetime.now(timezone.utc).isoformat()}', '',
        '**Alcance:** trabajo de preparación y predicción de defectos del Tema 8; se conserva sin cambios el Entregable 1 de Sara.', '',
        '## Procedimientos aplicados', '',
        '1. Lectura en modo no destructivo de los cinco CSV originales.',
        f'2. Comprobación de SHA-256 contra diagnóstico: {"obligatoria" if verificar_hash else "desactivada bajo petición (consultar manifiesto)"}.',
        '3. Conversión de las 21 métricas a tipos numéricos y estandarización de etiqueta a `defectuoso` (0/1).',
        '4. Eliminación SOLO de filas exactamente idénticas en métricas y etiqueta, manteniendo la primera aparición.',
        '5. Conservación de entradas de métricas idénticas con etiquetas diferentes: no inventamos la etiqueta verdadera.',
        '6. Conservación de valores atípicos: su detección estadística no implica error.',
        '7. Separación de JM1 en entrenamiento y prueba utilizando grupos de métricas iguales para evitar fugas.',
        '8. NO se aplica escalado, normalización por media o imputación global: se hará dentro de los pipelines de entrenamiento, ajustando solo con train.', '',
        '## Registros después de quitar duplicados exactos', '',
        '| Dataset | Registros originales | Registros preparados | Duplicados eliminados | Defectuosos preparados | % defectuosos preparados | Grupos contradictorios |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for r in manifest:
        l.append(f'| {r["dataset"]} | {r["filas_originales"]:,} | {r["filas_preparadas"]:,} | '
                 f'{r["duplicados_exactos_eliminados"]:,} | {r["defectuosos_preparados"]:,} | '
                 f'{r["porcentaje_defectuosos_preparados"]}% | {r["grupos_metricas_con_etiquetas_contradictorias"]:,} |')
    l += ['', '## División de JM1 (dataset candidato inicial)', '',
          f'- Entrenamiento: **{split["filas_entrenamiento"]:,} registros**, {split["tasa_defectos_entrenamiento"]}% defectuosos.',
          f'- Prueba: **{split["filas_prueba"]:,} registros**, {split["tasa_defectos_prueba"]}% defectuosos.',
          f'- Proporción real de prueba: **{split["porcentaje_prueba_real"]}%**.',
          f'- Grupos de métricas compartidos: **{split["grupos_de_metricas_compartidos"]}**.', '',
          '## Decisiones justificadas', '',
          '- **JM1** se elige como primer candidato por su tamaño. La selección final del dataset/modelo requiere evaluar rendimiento real.',
          '- **No se fusionan** CM1, JM1, KC1, KC2 y PC1: algunas columnas tienen grafías distintas y su equivalencia semántica no se estableció.',
          '- **Desbalance de clases:** la comparación de modelos deberá reportar Recall, Precision, F1 y matriz de confusión; Accuracy sola no basta.',
          '- **Contradicciones:** quedan registradas en archivos de auditoría; un vector con ambas etiquetas no debe ubicarse simultáneamente en train y test.',
          '- **Escalado y datos faltantes:** se hará en etapa de modelado con pipelines, evitando filtraciones del conjunto de prueba.',
          '- **Reproducibilidad:** revisar SHA-256 y `jm1_division.json` antes de integrar.', '',
          '## Archivos para entregar al siguiente componente', '',
          '- `*_preparado.csv`: versión limpia por dataset, sin duplicados exactos, con etiqueta binaria.',
          '- `*_auditoria.csv`: fuente, duplicación y contradicciones por fila original.',
          '- `jm1_entrenamiento.csv` y `jm1_prueba.csv`: conjuntos separados para entrenar y evaluar.',
          '- `jm1_mapa_particiones.csv`: mapa de grupos; no es dato de entrada del modelo.',
          '- `jm1_division.json` y `manifiesto_preparacion.json`: decisiones y trazabilidad.', '',
          '**Aviso:** este reporte describe los resultados de ejecutar el programa con los CSV originales. '
          'El archivo `resultados.zip` del diagnóstico, por sí solo, NO contiene todas las filas necesarias para construir estos CSV.']
    ruta.write_text('\n'.join(l)+'\n', encoding='utf-8')


def main() -> None:
    p = argparse.ArgumentParser(description='Preparar NASA PROMISE sin alterar originales')
    p.add_argument('--carpeta-datos', type=Path, default=RAIZ/'datos_originales')
    p.add_argument('--salida', type=Path, default=RAIZ/'datos_preparados')
    p.add_argument('--diagnostico', type=Path, default=RAIZ/'resultados_diagnostico')
    p.add_argument('--sin-verificar-hash', action='store_true', help='Solo para versiones diferentes del repositorio; registrar diferencia')
    a = p.parse_args()
    origen, destino = a.carpeta_datos.resolve(), a.salida.resolve()
    validar_rutas(origen,destino)
    diagnostico = cargar_diagnostico(a.diagnostico.resolve())
    if set(DATASETS)-set(diagnostico):
        raise ValueError('Diagnóstico no contiene los cinco datasets originales.')
    for n in DATASETS:
        if not (origen/f'{n}.csv').exists():
            raise FileNotFoundError(f'Falta {origen/f"{n}.csv"}. Descarga originales con python descargar_datasets.py')
    destino.mkdir(parents=True,exist_ok=True)
    manifest = []
    jm1 = None
    for n in DATASETS:
        base, estado = preparar_un_dataset(n, origen/f'{n}.csv', destino, diagnostico[n], not a.sin_verificar_hash)
        manifest.append(estado)
        if n=='jm1': jm1=base
        print(f'{n.upper()}: {estado["filas_originales"]:,} originales -> '
              f'{estado["filas_preparadas"]:,} preparados; '
              f'eliminados {estado["duplicados_exactos_eliminados"]:,} duplicados exactos; '
              f'{estado["grupos_metricas_con_etiquetas_contradictorias"]} grupos conflictivos conservados')
    division = dividir_jm1(jm1,destino)
    guardar_json(destino/'manifiesto_preparacion.json', {
        'fuente': 'https://github.com/ApoorvaKrisna/NASA-promise-dataset-repository',
        'verificacion_hash_exigida': not a.sin_verificar_hash,
        'datasets': manifest,
        'division_jm1': division,
    })
    generar_reporte(destino/'reporte_preparacion.md',manifest,division, not a.sin_verificar_hash)
    print(f'JM1: entrenamiento={division["filas_entrenamiento"]:,} '
          f'prueba={division["filas_prueba"]:,} '
          f'grupos_compartidos={division["grupos_de_metricas_compartidos"]}')
    print('Proceso terminado. Archivos creados EN:',destino)


if __name__=='__main__':
    main()
