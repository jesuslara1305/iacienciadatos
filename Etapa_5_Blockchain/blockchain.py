"""CLI de la cadena local académica del Proyecto IACD."""
from __future__ import annotations
import argparse
import copy
import json
import sys
from pathlib import Path
from blockchain_core import (
    agregar, cadena_nueva, cargar, comparar_archivo, guardar,
    registro_desde_csv, validar,
)

BASE=Path(__file__).resolve().parent

def imprimir(d):
    print(json.dumps(d, ensure_ascii=False, indent=2))

def cli(argv=None):
    p=argparse.ArgumentParser(description='Demostración de trazabilidad SHA-256 / Blockchain local')
    s=p.add_subparsers(dest='accion',required=True)
    reg=s.add_parser('registrar', help='Guardar huellas y resultados ML')
    reg.add_argument('--csv',type=Path,required=True)
    reg.add_argument('--modelo',type=Path)
    reg.add_argument('--cadena',type=Path,default=BASE/'datos'/'cadena.json')
    ver=s.add_parser('verificar',help='Verificar enlaces y hashes de la cadena')
    ver.add_argument('--cadena',type=Path,default=BASE/'datos'/'cadena.json')
    comp=s.add_parser('verificar-fuente',help='Comparar archivo original con el hash registrado')
    comp.add_argument('--cadena',type=Path,default=BASE/'datos'/'cadena.json')
    comp.add_argument('--csv',type=Path,required=True)
    comp.add_argument('--modelo',type=Path)
    comp.add_argument('--indice',type=int)
    demo=s.add_parser('demostrar-alteracion',help='Modificar SOLO una COPIA de la cadena')
    demo.add_argument('--cadena',type=Path,default=BASE/'datos'/'cadena.json')
    demo.add_argument('--salida',type=Path,default=BASE/'evidencias'/'cadena_alterada_copia.json')
    args=p.parse_args(argv)
    if args.accion=='registrar':
        c=cargar(args.cadena) if args.cadena.exists() else cadena_nueva()
        dato=registro_desde_csv(args.csv,args.modelo)
        b=agregar(c,dato)
        guardar(args.cadena,c)
        imprimir({'resultado':'REGISTRADO','bloque':b['indice'],'predicciones':dato['cantidad_predicciones'],'sha256_fuente':dato['sha256_archivo'],'hash_bloque':b['hash_bloque'],'cadena':str(args.cadena)})
        return 0
    if args.accion=='verificar':
        # Se carga sin validación para poder mostrar errores en una cadena manipulada.
        c=json.loads(args.cadena.read_text(encoding='utf-8'))
        errores=validar(c)
        imprimir({'integro':not errores,'bloques':len(c.get('bloques',[])),'errores':errores})
        return 0 if not errores else 2
    if args.accion=='verificar-fuente':
        c=cargar(args.cadena)
        res=comparar_archivo(c,args.csv,args.indice,args.modelo)
        imprimir(res)
        return 0 if res['integro'] else 2
    if args.accion=='demostrar-alteracion':
        c=cargar(args.cadena)
        if len(c['bloques'])<2:
            raise ValueError('Primero registra al menos un lote ML')
        muestra=copy.deepcopy(c)
        original=muestra['bloques'][1]['dato']['cantidad_predicciones']
        muestra['bloques'][1]['dato']['cantidad_predicciones']=original+1
        args.salida.parent.mkdir(parents=True,exist_ok=True)
        args.salida.write_text(json.dumps(muestra,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        errores=validar(muestra)
        imprimir({'cadena_original_valida':not validar(c),'copia_manipulada':str(args.salida),'alteracion_detectada':bool(errores),'errores':errores})
        return 0 if errores else 2
    return 1

if __name__=='__main__':
    try:
        sys.exit(cli())
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as exc:
        print('ERROR:',exc,file=sys.stderr)
        sys.exit(1)
