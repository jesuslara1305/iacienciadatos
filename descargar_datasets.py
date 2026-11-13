"""Descarga los CSV originales de NASA PROMISE sin modificar archivos existentes.

Ejecutar: python descargar_datasets.py
Si ya existe un CSV, NO lo sobrescribe. Se puede descargar manualmente y
colocar en datos_originales/ si no hay acceso a GitHub desde Python.
"""
from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / 'datos_originales'
BASE = 'https://raw.githubusercontent.com/ApoorvaKrisna/NASA-promise-dataset-repository/main'
ARCHIVOS = ('cm1.csv', 'jm1.csv', 'kc1.csv', 'kc2.csv', 'pc1.csv')


def sha256(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            digest.update(bloque)
    return digest.hexdigest()


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    print('NASA PROMISE: descarga no destructiva de los cinco CSV originales.')
    for nombre in ARCHIVOS:
        ruta = DESTINO / nombre
        if ruta.exists():
            print(f'CONSERVADO: {nombre} ({ruta.stat().st_size:,} bytes; SHA-256 {sha256(ruta)[:16]}...)')
            continue
        url = f'{BASE}/{nombre}'
        try:
            solicitud = urllib.request.Request(
                url, headers={'User-Agent': 'Mozilla/5.0 NASA-PROMISE-academic-analysis'}
            )
            with urllib.request.urlopen(solicitud, timeout=40) as respuesta:
                contenido = respuesta.read()
            if not contenido.lower().startswith(b'loc,'):
                raise ValueError('Contenido inesperado: no parece un CSV NASA PROMISE.')
            # Escritura exclusiva: evita sobreescribir incluso si otro proceso crea el archivo.
            try:
                with ruta.open('xb') as archivo:
                    archivo.write(contenido)
            except FileExistsError:
                print(f'CONSERVADO: {nombre}; ya existía antes de guardarlo.')
                continue
            print(f'DESCARGADO: {nombre} ({len(contenido):,} bytes; SHA-256 {sha256(ruta)[:16]}...)')
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
            print(f'ERROR con {nombre}: {error}')
            print(f'  Descarga manual: {url}')
    print(f'Carpeta de originales: {DESTINO}')


if __name__ == '__main__':
    main()
