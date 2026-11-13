"""Prueba interactiva de un reporte individual, apta para futura integración por API."""
from __future__ import annotations
import argparse
import json
from pnl_core import limpiar_texto, sentimiento_heuristico, extraer_entidades, resumen_individual, tokens


def procesar_reporte(titulo: str, descripcion: str) -> dict:
    t, d = limpiar_texto(titulo), limpiar_texto(descripcion)
    texto = (t + ". " + d).strip(". ")
    if len(texto) < 5:
        raise ValueError("Introduce un reporte más largo.")
    s = sentimiento_heuristico(texto)
    e = extraer_entidades(texto)
    return {
        "titulo": t, "texto_limpio": texto, "tokens": tokens(texto),
        "sentimiento": s, "entidades": e,
        "reporte_generado": resumen_individual(t, d, s["sentimiento"], e),
        "aviso": "Análisis heurístico textual independiente de predicción NASA PROMISE; no determina severidad."
    }


def main():
    p = argparse.ArgumentParser(description="Analizar una incidencia técnica escrita")
    p.add_argument("--titulo", required=True)
    p.add_argument("--descripcion", required=True)
    a = p.parse_args()
    print(json.dumps(procesar_reporte(a.titulo, a.descripcion), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
