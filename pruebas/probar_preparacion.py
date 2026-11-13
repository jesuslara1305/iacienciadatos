"""Pruebas automáticas con registros SINTÉTICOS (no son los NASA reales)."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COLUMNAS = ['loc','v(g)','ev(g)','iv(g)','n','v','l','d','i','e','b','t','lOCode',
            'lOComment','lOBlank','locCodeAndComment','uniq_Op','uniq_Opnd','total_Op','total_Opnd','branchCount']


def main():
    rng = np.random.default_rng(7)
    with tempfile.TemporaryDirectory() as temporal:
        raiz = Path(temporal)
        fuente, destino, diag = raiz/'originales', raiz/'salida', raiz/'diagnostico'
        for d in (fuente, destino, diag): d.mkdir()
        manifest = []
        for n in ('cm1','jm1','kc1','kc2','pc1'):
            filas = []
            for g in range(75):
                entradas = dict(zip(COLUMNAS,(rng.integers(1,200, size=21) + g/1000).tolist()))
                etiqueta = 1 if g%5 == 0 else 0
                fila = dict(entradas)
                fila['problems' if n=='kc2' else 'defects'] = ('yes' if etiqueta else 'no') if n=='kc2' else ('true' if etiqueta else 'false')
                filas.append(fila)
                # Repetición exacta intencional en todos los datasets.
                if g%4==0: filas.append(dict(fila))
                # Grupo igual con etiqueta distinta para auditar la contradicción.
                if g%13==0:
                    contraria = dict(fila)
                    contraria['problems' if n=='kc2' else 'defects'] = ('no' if etiqueta else 'yes') if n=='kc2' else ('false' if etiqueta else 'true')
                    filas.append(contraria)
            pd.DataFrame(filas).to_csv(fuente/f'{n}.csv',index=False)
            p = fuente/f'{n}.csv'
            manifest.append(dict(dataset=n.upper(),archivo=p.name,
                                 filas=len(filas),duplicados_exactos=pd.DataFrame(filas).duplicated().sum(),
                                 sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        pd.DataFrame(manifest).to_csv(diag/'resumen_datasets.csv', index=False)
        original_hash = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fuente.glob('*.csv')}
        run = subprocess.run([sys.executable,str(ROOT/'preparar_datos.py'),
                              '--carpeta-datos',str(fuente), '--salida',str(destino),
                              '--diagnostico',str(diag)], capture_output=True,text=True)
        assert run.returncode == 0, run.stdout + '\n' + run.stderr
        preparadas = pd.read_csv(destino/'jm1_preparado.csv')
        original = pd.read_csv(fuente/'jm1.csv')
        assert len(preparadas) == len(original) - original.duplicated().sum()
        assert set(preparadas['defectuoso']) == {0,1}
        assert preparadas.duplicated().sum()==0
        assert (pd.read_csv(destino/'jm1_auditoria.csv')
                ['grupo_con_etiquetas_contradictorias'].sum())>0
        ent = pd.read_csv(destino/'jm1_entrenamiento.csv')
        prue = pd.read_csv(destino/'jm1_prueba.csv')
        assert len(ent)+len(prue) == len(preparadas)
        assert set(pd.util.hash_pandas_object(ent.drop(columns='defectuoso'),index=False)).isdisjoint(
            set(pd.util.hash_pandas_object(prue.drop(columns='defectuoso'),index=False)))
        assert all(hashlib.sha256(p.read_bytes()).hexdigest()==original_hash[p.name] for p in fuente.glob('*.csv'))
        print(run.stdout)
        print('OK: los originales no cambiaron; etiquetas, duplicados, auditoría y grupos disjuntos verificados.')


if __name__=='__main__':
    main()
