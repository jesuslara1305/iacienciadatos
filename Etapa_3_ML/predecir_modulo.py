"""Predice defectos de nuevos módulos. Cargar solo modelos generados por ti."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

RAIZ=Path(__file__).resolve().parent

def predecir_dataframe(df: pd.DataFrame, ruta_modelo: Path | None=None, ruta_metadata: Path | None=None):
    ruta_modelo=Path(ruta_modelo or RAIZ/'modelos'/'modelo_defectos.joblib')
    ruta_metadata=Path(ruta_metadata or RAIZ/'modelos'/'modelo_metadata.json')
    meta=json.loads(ruta_metadata.read_text(encoding='utf-8'))
    columnas=meta['caracteristicas']
    faltan=[c for c in columnas if c not in df.columns]
    if faltan:
        raise ValueError('Faltan las métricas: '+', '.join(faltan))
    X=df[columnas].apply(pd.to_numeric,errors='raise')
    # Los archivos joblib son pickle: cargar únicamente ficheros de origen confiable.
    modelo=joblib.load(ruta_modelo)
    y=modelo.predict(X).astype(int)
    resultado=pd.DataFrame({'prediccion':y,'interpretacion':np.where(y==1,'Posible defecto','Sin defecto previsto')})
    if hasattr(modelo,'predict_proba'):
        resultado['probabilidad_defecto_no_calibrada']=modelo.predict_proba(X)[:,1]
    else:
        resultado['puntaje_decision_no_probabilidad']=modelo.decision_function(X)
    return resultado,meta

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Predicción de nuevos módulos de software')
    parser.add_argument('--archivo',type=Path,required=True,help='CSV con 21 métricas de módulos nuevos')
    parser.add_argument('--salida',type=Path,default=RAIZ/'resultados_ml'/'predicciones_nuevas.csv')
    args=parser.parse_args()
    datos=pd.read_csv(args.archivo)
    preds,meta=predecir_dataframe(datos)
    args.salida.parent.mkdir(parents=True,exist_ok=True)
    preds.to_csv(args.salida,index=False)
    print('Modelo:',meta['modelo_seleccionado'])
    print(preds.to_string(index=False))
    print('Resultados:',args.salida)
