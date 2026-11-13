"""Blockchain local académica de integridad, no una red descentralizada.

No ofrece inmutabilidad frente a un adversario capaz de reescribir toda la cadena;
requiere un anclaje independiente del hash final para esa propiedad.
"""
from __future__ import annotations
import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = 1
CAMPOS = {'indice', 'fecha_utc', 'hash_anterior', 'dato', 'hash_dato', 'hash_bloque'}

def json_canonico(valor: Any) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def sha256_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def huella_dato(dato: dict) -> str:
    return sha256_texto(json_canonico(dato))

def huella_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with Path(ruta).open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            h.update(bloque)
    return h.hexdigest()

def hash_bloque(bloque: dict) -> str:
    return sha256_texto(json_canonico({k: v for k, v in bloque.items() if k != 'hash_bloque'}))

def crear_bloque(indice: int, previo: str, dato: dict) -> dict:
    bloque = {
        'indice': indice,
        'fecha_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'hash_anterior': previo,
        'dato': dato,
        'hash_dato': huella_dato(dato),
    }
    bloque['hash_bloque'] = hash_bloque(bloque)
    return bloque

def cadena_nueva() -> dict:
    genesis = crear_bloque(0, '0' * 64, {'tipo': 'genesis', 'descripcion': 'Cadena local de trazabilidad para Proyecto IACD'})
    return {'version': VERSION, 'tipo': 'blockchain_academica_local', 'bloques': [genesis]}

def validar(cadena: dict) -> list[str]:
    errores = []
    if not isinstance(cadena, dict) or cadena.get('version') != VERSION or cadena.get('tipo') != 'blockchain_academica_local':
        return ['Encabezado o versión de la cadena no válido']
    bloques = cadena.get('bloques')
    if not isinstance(bloques, list) or not bloques:
        return ['La cadena no tiene bloques']
    for i, b in enumerate(bloques):
        if not isinstance(b, dict) or set(b) != CAMPOS:
            errores.append(f'Bloque {i}: campos incorrectos')
            continue
        if b['indice'] != i:
            errores.append(f'Bloque {i}: índice incorrecto')
        if not isinstance(b['dato'], dict):
            errores.append(f'Bloque {i}: dato no es objeto')
        else:
            try:
                if b['hash_dato'] != huella_dato(b['dato']):
                    errores.append(f'Bloque {i}: datos alterados (hash_dato)')
            except (TypeError, ValueError):
                errores.append(f'Bloque {i}: datos no serializables')
        esperado = '0' * 64 if i == 0 else bloques[i-1].get('hash_bloque') if isinstance(bloques[i-1], dict) else None
        if b['hash_anterior'] != esperado:
            errores.append(f'Bloque {i}: enlace con bloque anterior incorrecto')
        try:
            if b['hash_bloque'] != hash_bloque(b):
                errores.append(f'Bloque {i}: contenido de bloque modificado')
        except (ValueError, TypeError):
            errores.append(f'Bloque {i}: bloque no serializable')
    if len(bloques) > 0 and isinstance(bloques[0], dict) and bloques[0].get('dato', {}).get('tipo') != 'genesis':
        errores.append('Bloque 0: génesis incorrecto')
    return errores

def guardar(ruta: Path, cadena: dict) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    contenido = json.dumps(cadena, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=ruta.parent, prefix='.cadena_', suffix='.tmp', delete=False) as f:
            tmp = f.name
            f.write(contenido + '\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, ruta)
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)

def cargar(ruta: Path) -> dict:
    with Path(ruta).open('r', encoding='utf-8') as f:
        cadena = json.load(f)
    errores = validar(cadena)
    if errores:
        raise ValueError('Cadena corrupta: ' + '; '.join(errores[:5]))
    return cadena

def agregar(cadena: dict, dato: dict) -> dict:
    errores = validar(cadena)
    if errores:
        raise ValueError('No se registra sobre una cadena inválida: ' + '; '.join(errores[:5]))
    if not isinstance(dato, dict) or 'tipo' not in dato:
        raise ValueError('El registro debe ser un objeto con campo tipo')
    anterior = cadena['bloques'][-1]['hash_bloque']
    b = crear_bloque(len(cadena['bloques']), anterior, dato)
    cadena['bloques'].append(b)
    return b

def leer_predicciones_csv(ruta: Path) -> tuple[list[dict], list[str]]:
    with Path(ruta).open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or 'prediccion' not in reader.fieldnames:
            raise ValueError('CSV debe contener columna prediccion')
        fields = list(reader.fieldnames)
        if len(fields) != len(set(fields)):
            raise ValueError('Columnas CSV duplicadas')
        filas = list(reader)
        if not 1 <= len(filas) <= 10000:
            raise ValueError('Se requieren entre 1 y 10,000 predicciones')
        if any(fila['prediccion'] not in ('0','1') for fila in filas):
            raise ValueError('Prediccion debe contener 0 o 1')
        if any(None in fila for fila in filas):
            raise ValueError('CSV contiene columnas extra inesperadas')
        return filas, fields

def registro_desde_csv(ruta: Path, modelo: Path | None = None) -> dict:
    ruta = Path(ruta)
    filas, columnas = leer_predicciones_csv(ruta)
    res = {
        'tipo': 'lote_predicciones_ml',
        'origen_archivo': ruta.name,
        'sha256_archivo': huella_archivo(ruta),
        'cantidad_predicciones': len(filas),
        'total_predichos_defectuosos': sum(f['prediccion']=='1' for f in filas),
        'columnas': columnas,
        'predicciones': filas,
    }
    if modelo is not None:
        res['modelo_archivo'] = Path(modelo).name
        res['sha256_modelo'] = huella_archivo(modelo)
    return res

def comparar_archivo(cadena: dict, ruta: Path, indice: int | None = None, modelo: Path | None = None) -> dict:
    errores = validar(cadena)
    if errores:
        return {'integro': False, 'errores': errores}
    if indice is None:
        candidatos = [b for b in cadena['bloques'] if b['dato'].get('tipo') == 'lote_predicciones_ml']
        if not candidatos:
            return {'integro': False, 'errores': ['Sin lotes de predicción registrados']}
        bloque = candidatos[-1]
    else:
        if indice < 1 or indice >= len(cadena['bloques']):
            return {'integro': False, 'errores': ['Índice no existe o corresponde a génesis']}
        bloque = cadena['bloques'][indice]
        if bloque['dato'].get('tipo') != 'lote_predicciones_ml':
            return {'integro': False, 'errores': ['El bloque no es un lote de predicciones']}
    dato = bloque['dato']
    actual = huella_archivo(Path(ruta))
    errores = []
    if actual != dato['sha256_archivo']:
        errores.append('La fuente CSV fue modificada respecto del registro')
    if modelo is not None:
        if 'sha256_modelo' not in dato or huella_archivo(Path(modelo)) != dato['sha256_modelo']:
            errores.append('El modelo ha cambiado o no estaba registrado')
    return {'integro': not errores, 'indice': bloque['indice'], 'hash_registrado': dato['sha256_archivo'], 'hash_actual': actual, 'errores': errores}
