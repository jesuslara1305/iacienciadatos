"""Etapa 3: compara tres clasificadores de defectos con JM1 NASA PROMISE.

Todos los ajustes (mediana/escala) ocurren dentro de Pipeline sobre train.
La selección del modelo se hace EXCLUSIVAMENTE con CV agrupada en train.
El conjunto test se usa una única vez, al final, para evaluación final.
No toca datos_originales/, ni datos_preparados/ ni el Entregable 1.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, classification_report,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
    ConfusionMatrixDisplay, PrecisionRecallDisplay, RocCurveDisplay)
from sklearn.model_selection import StratifiedGroupKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

RAIZ = Path(__file__).resolve().parent
DATOS_PREPARADOS_DEFECTO = (RAIZ/'datos_preparados' if (RAIZ/'datos_preparados').exists()
                            else RAIZ.parent/'datos_preparados')
ETIQUETA = 'defectuoso'
SEMILLA = 42


def hash_archivo(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()


def carga_y_valida(carpeta: Path):
    tr_path = carpeta / 'jm1_entrenamiento.csv'
    te_path = carpeta / 'jm1_prueba.csv'
    if not tr_path.is_file() or not te_path.is_file():
        raise FileNotFoundError('No encuentro jm1_entrenamiento.csv y jm1_prueba.csv en '+str(carpeta))
    train = pd.read_csv(tr_path)
    test = pd.read_csv(te_path)
    if ETIQUETA not in train.columns or list(train.columns) != list(test.columns):
        raise ValueError('Columnas diferentes o falta la variable objetivo defectuoso.')
    cols = [c for c in train.columns if c != ETIQUETA]
    if len(cols) != 21:
        raise ValueError(f'Se esperaban 21 métricas y se encontraron {len(cols)}.')
    if train[cols].isna().any().any() or test[cols].isna().any().any():
        print('AVISO: faltantes detectados; los pipelines los imputarán SOLO desde train')
    for nombre, df in [('train',train),('test',test)]:
        if not df[cols].apply(lambda c: pd.api.types.is_numeric_dtype(c)).all():
            raise ValueError(f'{nombre}: hay columnas de métricas no numéricas.')
        if df[ETIQUETA].isna().any() or not set(df[ETIQUETA].unique()).issubset({0,1}):
            raise ValueError(f'{nombre}: la etiqueta debe ser 0 o 1.')
        if df.duplicated().any():
            raise ValueError(f'{nombre}: hay filas completas duplicadas; revisa etapa 2.')
    # Cada vector idéntico, incluso con etiqueta distinta, debe quedarse en una sola partición.
    grupos_train = pd.util.hash_pandas_object(train[cols], index=False).to_numpy()
    grupos_test = pd.util.hash_pandas_object(test[cols], index=False).to_numpy()
    compartidos = set(grupos_train) & set(grupos_test)
    if compartidos:
        raise ValueError(f'FUGA DETECTADA: {len(compartidos)} grupos de métricas compartidos entre train y test')
    division_path = carpeta / 'jm1_division.json'
    if division_path.exists():
        division = json.loads(division_path.read_text(encoding='utf-8'))
        for campo, real in [('filas_entrenamiento',len(train)),('filas_prueba',len(test))]:
            if int(division[campo]) != real:
                raise ValueError('La partición no coincide con jm1_division.json ('+campo+')')
    return train,test,cols,grupos_train,{
        'sha256_entrenamiento': hash_archivo(tr_path),
        'sha256_prueba': hash_archivo(te_path),
        'filas_entrenamiento': int(len(train)),
        'filas_prueba': int(len(test)),
        'clase_positiva_entrenamiento': int(train[ETIQUETA].sum()),
        'clase_positiva_prueba': int(test[ETIQUETA].sum()),
        'grupos_entre_particiones': len(compartidos),
    }


def modelos():
    return {
        'Regresion logistica': Pipeline([
            ('imputar',SimpleImputer(strategy='median')),
            ('escalar',StandardScaler()),
            ('clasificador', LogisticRegression(C=1.0, max_iter=3000, class_weight='balanced',random_state=SEMILLA))]),
        'Random Forest': Pipeline([
            ('imputar',SimpleImputer(strategy='median')),
            ('clasificador',RandomForestClassifier(n_estimators=200, max_depth=12, min_samples_leaf=2,
                class_weight='balanced_subsample', n_jobs=2,random_state=SEMILLA))]),
        'SVM (RBF)': Pipeline([
            ('imputar',SimpleImputer(strategy='median')),
            ('escalar',StandardScaler()),
            ('clasificador',SVC(C=1.0, kernel='rbf', gamma='scale', class_weight='balanced',random_state=SEMILLA))]),
    }


def resultados_clasificacion(y_real, pred, score=None, probs=False):
    tn,fp,fn,tp=confusion_matrix(y_real,pred,labels=[0,1]).ravel()
    res={'accuracy':float(accuracy_score(y_real,pred)),
         'precision':float(precision_score(y_real,pred,zero_division=0)),
         'recall':float(recall_score(y_real,pred,zero_division=0)),
         'f1':float(f1_score(y_real,pred,zero_division=0)),
         'verdaderos_negativos':int(tn),'falsos_positivos':int(fp),
         'falsos_negativos':int(fn),'verdaderos_positivos':int(tp)}
    if score is not None:
        res['roc_auc']=float(roc_auc_score(y_real,score))
        res['average_precision']=float(average_precision_score(y_real,score))
    return res


def savefig(path):
    plt.tight_layout()
    plt.savefig(path,dpi=150,bbox_inches='tight')
    plt.close()


def entrenar(carpeta_datos: Path, raiz: Path):
    train,test,cols,grupos,origen=carga_y_valida(carpeta_datos)
    X_train, y_train=train[cols], train[ETIQUETA].astype(int)
    X_test, y_test=test[cols], test[ETIQUETA].astype(int)
    mod_dir = raiz / 'modelos'; res_dir=raiz / 'resultados_ml'; doc_dir=raiz / 'documentacion_ml'
    for carpeta in [mod_dir,res_dir,doc_dir]: carpeta.mkdir(parents=True,exist_ok=True)

    # Verificamos que todas las particiones CV contienen dos clases. El conjunto test NO participa.
    cv=StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=SEMILLA)
    folds=list(cv.split(X_train,y_train,groups=grupos))
    resumen_folds=[]
    for k,(idx_tr,idx_va) in enumerate(folds,1):
        if len(set(y_train.iloc[idx_tr]))!=2 or len(set(y_train.iloc[idx_va]))!=2:
            raise ValueError('Un fold de CV no contiene ambas clases.')
        if set(grupos[idx_tr]) & set(grupos[idx_va]):
            raise ValueError('Fuga de métricas entre folds de CV.')
        resumen_folds.append({'fold':k,'filas_entrenamiento':len(idx_tr),'filas_validacion':len(idx_va),
                              'positivos_validacion':int(y_train.iloc[idx_va].sum())})

    scoring={'f1':'f1','recall':'recall','precision':'precision','accuracy':'accuracy','roc_auc':'roc_auc'}
    comparacion_cv=[]; entrenados={}; evaluacion=[]; predicciones={}; scores={}
    for nombre,pipe in modelos().items():
        print(f'Validación cruzada: {nombre}...',flush=True)
        resultado_cv=cross_validate(pipe,X_train,y_train,cv=folds,scoring=scoring,n_jobs=1,
                                    error_score='raise',return_train_score=False)
        fila={'modelo':nombre}
        for s in scoring:
            fila[f'cv_{s}_promedio']=float(np.mean(resultado_cv['test_'+s]))
            fila[f'cv_{s}_desviacion']=float(np.std(resultado_cv['test_'+s]))
        comparacion_cv.append(fila)
        print(f"    CV F1={fila['cv_f1_promedio']:.4f}, Recall={fila['cv_recall_promedio']:.4f}",flush=True)
        print(f'Entrenando con todas las filas de train: {nombre}...',flush=True)
        pipe.fit(X_train,y_train)
        entrenados[nombre]=pipe
    # Selección por F1 de validación cruzada. No se ha accedido a y_test para ajustar ni seleccionar.
    elegido=max(comparacion_cv,key=lambda r:(r['cv_f1_promedio'],r['cv_recall_promedio']))['modelo']
    joblib.dump(entrenados[elegido],mod_dir/'modelo_defectos.joblib',compress=3)
    nombres_archivo={'Regresion logistica':'modelo_regresion_logistica.joblib',
                     'Random Forest':'modelo_random_forest.joblib','SVM (RBF)':'modelo_svm.joblib'}
    for nombre,pipe in entrenados.items():
        joblib.dump(pipe,mod_dir/nombres_archivo[nombre],compress=3)
    print('Modelo seleccionado por CV en entrenamiento:',elegido,flush=True)

    # Con el modelo seleccionado, se realiza una evaluación única en test.
    # Los otros dos también se reportan para fines académicos, pero su prueba no modifica la selección.
    for nombre,pipe in entrenados.items():
        preds=pipe.predict(X_test).astype(int)
        tiene_proba=hasattr(pipe,'predict_proba')
        score=pipe.predict_proba(X_test)[:,1] if tiene_proba else pipe.decision_function(X_test)
        resultado=resultados_clasificacion(y_test,preds,score,probs=tiene_proba)
        resultado['modelo']=nombre
        resultado['seleccionado_por_cv']=bool(nombre==elegido)
        evaluacion.append(resultado)
        predicciones[nombre]=preds
        scores[nombre]=score
        ConfusionMatrixDisplay.from_predictions(y_test,preds,display_labels=['Sin defecto','Con defecto'],
                                                cmap='Blues',values_format='d')
        plt.title('Matriz de confusión — '+nombre)
        savefig(res_dir/('confusion_'+nombres_archivo[nombre].replace('modelo_','').replace('.joblib','.png')))
    # Línea base (clasificar todo como clase más frecuente) para contextualizar Accuracy.
    dummy=DummyClassifier(strategy='most_frequent').fit(X_train,y_train)
    baseline=resultados_clasificacion(y_test,dummy.predict(X_test))
    (res_dir/'linea_base.json').write_text(json.dumps(baseline,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    cv_df=pd.DataFrame(comparacion_cv).sort_values('cv_f1_promedio',ascending=False)
    cv_df.to_csv(res_dir/'comparacion_validacion_cruzada.csv',index=False)
    ev_df=pd.DataFrame(evaluacion).sort_values('f1',ascending=False)
    ev_df.to_csv(res_dir/'comparacion_prueba.csv',index=False)
    plt.figure(figsize=(9,5))
    ind=np.arange(len(evaluacion));ancho=0.24
    for i,metrica in enumerate(['precision','recall','f1']):
        plt.bar(ind+(i-1)*ancho,[r[metrica] for r in evaluacion],width=ancho,label=metrica.capitalize())
    plt.xticks(ind,[r['modelo'] for r in evaluacion]); plt.ylim(0,1);plt.ylabel('Valor de la métrica')
    plt.legend();plt.title('Comparación final en JM1 — conjunto de prueba')
    savefig(res_dir/'comparacion_modelos.png')

    plt.figure(figsize=(7,5))
    for nombre in entrenados:
        RocCurveDisplay.from_predictions(y_test,scores[nombre],name=nombre,ax=plt.gca())
    plt.title('Curvas ROC — conjunto de prueba')
    savefig(res_dir/'curvas_roc.png')
    plt.figure(figsize=(7,5))
    for nombre in entrenados:
        PrecisionRecallDisplay.from_predictions(y_test,scores[nombre],name=nombre,ax=plt.gca())
    plt.title('Curvas precisión-recall — conjunto de prueba')
    savefig(res_dir/'curvas_precision_recall.png')

    elegido_mod=entrenados[elegido]
    pred_df=pd.DataFrame({
        'registro_en_jm1_prueba':np.arange(1,len(test)+1),
        'etiqueta_real':y_test.to_numpy(),
        'prediccion':predicciones[elegido].astype(int),
    })
    if hasattr(elegido_mod,'predict_proba'):
        pred_df['probabilidad_defecto_no_calibrada']=scores[elegido]
    else:
        pred_df['puntaje_decision_no_probabilidad']=scores[elegido]
    pred_df.to_csv(res_dir/'predicciones_jm1_prueba.csv',index=False)
    X_test.head(5).to_csv(raiz/'ejemplos'/'ejemplo_nuevos_modulos.csv',index=False)
    metadata={
        'modelo_seleccionado':elegido,
        'criterio_seleccion':'Mayor promedio F1 clase defectuoso=1 en CV agrupada de entrenamiento; desempate por Recall',
        'cv_tipo':'StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42)',
        'cv_folds':resumen_folds,
        'caracteristicas':cols,
        'variable_objetivo':ETIQUETA,
        'etiquetas':{'0':'sin defecto registrado','1':'con defecto registrado'},
        'origen':origen,
        'algoritmos':[{'nombre':name,'parametros':pipe.get_params()['clasificador'].get_params()} for name,pipe in entrenados.items()],
        'versiones':{'python':platform.python_version(),'scikit_learn':sklearn.__version__,
                      'pandas':pd.__version__,'numpy':np.__version__,'joblib':joblib.__version__},
        'creado_utc':datetime.now(timezone.utc).isoformat(),
        'aviso':'El valor de predict_proba NO se calibró y no debe interpretarse como frecuencia real de defectos. '
                'Las decisiones SVM no son probabilidades. Validado inicialmente en NASA PROMISE JM1; no sustituye pruebas de software.'
    }
    (mod_dir/'modelo_metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    reporte=[
        '# Entregable 3 — Entrenamiento y evaluación de Machine Learning','',
        '## Objetivo','Clasificar módulos de software en **sin defectos (0)** y **con defectos (1)**, utilizando 21 métricas históricas del dataset JM1 de NASA PROMISE.','',
        '## Preparación','Los duplicados exactos se quitaron en etapa 2; se conservaron vectores con etiquetas contradictorias y valores atípicos. '
        'Se utilizó una división fija de 7,127 filas para entrenar y 1,781 para probar. '
        'El mismo vector de métricas nunca se comparte entre ambos conjuntos.','',
        '## Algoritmos','Se usaron Regresión Logística, Random Forest y SVM con kernel RBF. '
        'La regresión y SVM escalan las métricas; Random Forest no requiere escalado. '
        'Los pipelines imputan mediana y, cuando procede, estandarizan utilizando solo las filas de entrenamiento de cada fold. '
        'Se utilizaron pesos de clase balanceados por el desbalance de etiquetas.','',
        '## Selección sin fuga','La selección del modelo se efectuó únicamente con validación cruzada de 3 particiones agrupadas por identidad del vector de métricas. '
        'No se ajustaron modelos, hiperparámetros ni umbrales mirando el conjunto de prueba. '
        'Las configuraciones son iniciales, no el resultado de una búsqueda exhaustiva de hiperparámetros.','',
        '## Resultados de validación cruzada (solo entrenamiento)','',
        '| Algoritmo | F1 medio | Recall medio | Precision media | Accuracy media |',
        '|---|---:|---:|---:|---:|',
    ]
    for r in sorted(comparacion_cv,key=lambda x:-x['cv_f1_promedio']):
        reporte.append(f"| {r['modelo']} | {r['cv_f1_promedio']:.4f} | {r['cv_recall_promedio']:.4f} | {r['cv_precision_promedio']:.4f} | {r['cv_accuracy_promedio']:.4f} |")
    reporte += ['',f'**Modelo seleccionado por validación cruzada:** {elegido}.','',
                '## Resultados en test fijo (1,781 registros)','',
                '| Modelo | Accuracy | Precision | Recall | F1 | TN | FP | FN | TP | ROC AUC |',
                '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in evaluacion:
        reporte.append(f"| {r['modelo']} | {r['accuracy']:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | {r['f1']:.4f} | {r['verdaderos_negativos']} | {r['falsos_positivos']} | {r['falsos_negativos']} | {r['verdaderos_positivos']} | {r['roc_auc']:.4f} |")
    reporte += ['',f"**Línea base (siempre clase mayoritaria):** Accuracy {baseline['accuracy']:.4f}; Recall {baseline['recall']:.4f}; F1 {baseline['f1']:.4f}.",'',
        '## Interpretación de métricas',
        '- **Accuracy:** proporción total de aciertos; puede ser engañosa en clases desbalanceadas.',
        '- **Precision:** entre módulos señalados como defectuosos, proporción realmente defectuosa.',
        '- **Recall:** de todos los módulos defectuosos reales, proporción detectada.',
        '- **F1:** media armónica de precision y recall de la clase positiva.',
        '- **TN, FP, FN, TP:** verdaderos negativos, falsos positivos, falsos negativos y verdaderos positivos.',
        '- **ROC AUC:** separación entre clases sin depender del umbral de clasificación.','',
        '## Archivos generados','- `modelos/modelo_defectos.joblib`: pipeline seleccionado con preprocesamiento integrado.',
        '- `modelos/modelo_*`: los tres pipelines entrenados.',
        '- `modelos/modelo_metadata.json`: columnas, decisiones, versiones, hashes de origen.',
        '- `resultados_ml/comparacion_validacion_cruzada.csv`: métricas usadas para seleccionar.',
        '- `resultados_ml/comparacion_prueba.csv`: evaluación final de los tres.',
        '- `resultados_ml/predicciones_jm1_prueba.csv`: predicciones auditables.',
        '- `resultados_ml/*.png`: matrices y curvas.','',
        '## Limitaciones','1. Los datos NASA PROMISE son históricos y su distribución puede diferir de proyectos actuales.',
        '2. JM1 incluye métricas iguales con etiquetas diferentes: existe ruido o ambigüedad en esas observaciones.',
        '3. El riesgo estimado no prueba que existan defectos; es un apoyo a la priorización de pruebas.',
        '4. La evaluación se realizó dentro de JM1; no demuestra generalización a otros proyectos.',
        '5. La probabilidad de Regresión Logística o Random Forest NO ha sido calibrada; SVM ofrece un puntaje de decisión, no una probabilidad.',
        '6. Se usaron configuraciones iniciales; una optimización de hiperparámetros debe ocurrir solo dentro de entrenamiento.','',
        '## Evidencia de ejecución','Modelos serializados, predicciones CSV y gráficas construidas a partir del split real de JM1; '
        'la tabla de arriba proviene de la ejecución del código. Conservar una captura de la terminal de ejecución local.','']
    (doc_dir/'informe_resultados_ml.md').write_text('\n'.join(reporte),encoding='utf-8')
    print('\nEvaluación test final:')
    print(ev_df[['modelo','accuracy','precision','recall','f1','falsos_negativos']].to_string(index=False))
    print('\nGenerados resultados en: ',str(res_dir))
    return elegido,comparacion_cv,evaluacion


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Entrenar y evaluar 3 clasificadores NASA PROMISE JM1')
    parser.add_argument('--carpeta-datos',type=Path,default=DATOS_PREPARADOS_DEFECTO,
                        help='Directorio con jm1_entrenamiento.csv y jm1_prueba.csv')
    args=parser.parse_args()
    (RAIZ/'ejemplos').mkdir(parents=True,exist_ok=True)
    entrenar(args.carpeta_datos.resolve(),RAIZ)
