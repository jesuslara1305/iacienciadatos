"""Pruebas de integridad de los archivos de ML. Ejecución: python pruebas_ml.py"""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
from predecir_modulo import predecir_dataframe

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--carpeta-datos',type=Path,default=(root/'datos_preparados' if (root/'datos_preparados').exists() else root.parent/'datos_preparados'))
args=parser.parse_args()
train=pd.read_csv(args.carpeta_datos/'jm1_entrenamiento.csv')
test=pd.read_csv(args.carpeta_datos/'jm1_prueba.csv')
cols=[c for c in train if c!='defectuoso']
assert len(cols)==21, 'Se requieren 21 métricas'
assert len(train)==7127 and len(test)==1781, 'Tamaños inesperados de dataset'
assert set(pd.util.hash_pandas_object(train[cols],index=False)).isdisjoint(
    set(pd.util.hash_pandas_object(test[cols],index=False))), 'Vectores compartidos entre conjuntos'
result, metadata=predecir_dataframe(test[cols].head(10))
assert len(result)==10
assert result.prediccion.isin([0,1]).all()
pred_report=pd.read_csv(root/'resultados_ml'/'predicciones_jm1_prueba.csv')
assert (result.prediccion.to_numpy()==pred_report.prediccion.head(10).to_numpy()).all(), 'Predicciones no reproducibles'
print('CORRECTO: 21 métricas, particiones sin grupos comunes, modelo ejecutable y predicciones reproducibles.')
print('Modelo:',metadata['modelo_seleccionado'])
