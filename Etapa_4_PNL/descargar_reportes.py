"""Obtiene issues públicos de GitHub etiquetados como bug. No descarga PRs.

Atribución de origen conservada en columna source_url. Respeta rate limits y no
sobrescribe por defecto. El archivo resultante debe revisarse antes de publicarlo.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from pnl_core import limpiar_texto

BASE = Path(__file__).resolve().parent


def argumentos():
    p = argparse.ArgumentParser(description="Descargar reportes públicos de errores de GitHub")
    p.add_argument("--repositorio", default="microsoft/vscode", help="organizacion/repositorio, público")
    p.add_argument("--etiqueta", default="bug", help="etiqueta real existente en el repositorio")
    p.add_argument("--estado", choices=["open", "closed", "all"], default="all")
    p.add_argument("--max-reportes", type=int, default=180)
    p.add_argument("--max-paginas", type=int, default=6)
    p.add_argument("--salida", type=Path, default=BASE / "datos_textuales" / "reportes_github.csv")
    p.add_argument("--sobrescribir", action="store_true")
    return p.parse_args()


def main():
    a = argumentos()
    if not __import__("re").fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", a.repositorio):
        raise ValueError("Usa --repositorio propietario/nombre.")
    if not (1 <= a.max_reportes <= 1000 and 1 <= a.max_paginas <= 30):
        raise ValueError("Revisa los límites de --max-reportes y --max-paginas.")
    if a.salida.exists() and not a.sobrescribir:
        raise FileExistsError(f"No se sobrescribirá el archivo existente: {a.salida}. Usa --sobrescribir para reemplazarlo.")
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Proyecto-IACD-academico", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    registros = []
    for pagina in range(1, a.max_paginas + 1):
        params = urllib.parse.urlencode({"state": a.estado, "labels": a.etiqueta, "per_page": 100, "page": pagina, "direction": "desc", "sort": "created"})
        url = f"https://api.github.com/repos/{a.repositorio}/issues?{params}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                datos = json.load(response)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                raise RuntimeError("GitHub limitó las peticiones; inténtalo más tarde o usa GITHUB_TOKEN. No se generó ningún dataset nuevo.") from e
            raise RuntimeError(f"GitHub devolvió HTTP {e.code}; verifica el repositorio y la etiqueta.") from e
        except urllib.error.URLError as e:
            raise RuntimeError("No se pudo conectar con GitHub. Verifica tu conexión; también puedes usar un CSV propio.") from e
        if not isinstance(datos, list):
            raise RuntimeError("Formato de respuesta inesperado de GitHub.")
        if not datos:
            break
        for issue in datos:
            if "pull_request" in issue:  # La API incluye PR en /issues
                continue
            titulo = limpiar_texto(issue.get("title") or "")
            cuerpo = limpiar_texto(issue.get("body") or "")[:3000]
            if not titulo or len(titulo + cuerpo) < 25:
                continue
            registros.append({
                "id": issue.get("number"), "repositorio": a.repositorio,
                "source_url": issue.get("html_url", ""),
                "fecha": issue.get("created_at", ""),
                "etiquetas": "; ".join(label.get("name", "") for label in issue.get("labels", []) if isinstance(label, dict)),
                "titulo": titulo, "descripcion": cuerpo, "origen": "GitHub Issues REST API (reporte publico)",
            })
            if len(registros) >= a.max_reportes:
                break
        print(f"Página {pagina}: {len(datos)} elementos; {len(registros)} reportes válidos acumulados")
        if len(registros) >= a.max_reportes or len(datos) < 100:
            break
        time.sleep(0.2)
    if not registros:
        raise RuntimeError("No hay issues elegibles; comprueba la etiqueta. No se generó un archivo vacío.")
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    with a.salida.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(registros[0]))
        writer.writeheader()
        writer.writerows(registros)
    print(f"Listo: {len(registros)} reportes reales con URL de origen. CSV: {a.salida}")
    print("Nota: la disponibilidad pública no equivale a permiso de redistribución. Mantén enlaces a las fuentes.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, FileExistsError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
