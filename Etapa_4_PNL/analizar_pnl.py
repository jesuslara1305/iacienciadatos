"""Analiza CSV de reportes de software: TF-IDF + sentimiento + NER + reporte.

Datos NASA PROMISE NO tienen vínculo registro-a-registro con estos textos.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from pnl_core import limpiar_texto, sentimiento_heuristico, extraer_entidades, resumen_individual, resumen_general

BASE = Path(__file__).resolve().parent


def analizar(entrada: Path, salida: Path) -> dict:
    if not entrada.is_file():
        raise FileNotFoundError(f"No existe el CSV: {entrada}")
    df = pd.read_csv(entrada, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    oblig = {"titulo", "descripcion"}
    if not oblig.issubset(df.columns):
        raise ValueError(f"Faltan columnas obligatorias: {sorted(oblig - set(df.columns))}. Requeridas: titulo, descripcion")
    if df.empty:
        raise ValueError("El CSV está vacío.")
    inicial = len(df)
    for col in ["titulo", "descripcion"]:
        df[col] = df[col].map(limpiar_texto)
    df["texto"] = (df["titulo"] + ". " + df["descripcion"]).str.strip(". ")
    df = df[df["texto"].str.len() >= 10].copy()
    # URLs no repetidas cuando existen; en otros casos, contenido idéntico.
    if "source_url" in df.columns:
        url = df["source_url"].str.strip()
        tiene = url.ne("")
        con_url = df[tiene].drop_duplicates(subset=["source_url"], keep="first")
        sin_url = df[~tiene].drop_duplicates(subset=["texto"], keep="first")
        df = pd.concat([con_url, sin_url], ignore_index=True)
    else:
        df = df.drop_duplicates(subset=["texto"], keep="first").reset_index(drop=True)
    if df.empty:
        raise ValueError("No quedan textos válidos después de limpiar y eliminar duplicados.")
    origen = "GitHub Issues" if ("origen" in df.columns and df["origen"].str.contains("GitHub", case=False).any()) else "dataset proporcionado / ejemplos"
    simulado = entrada.stem.lower().startswith("reportes_sinteticos") or ("origen" in df.columns and df["origen"].str.contains("simulad", case=False).all())

    # TF-IDF sobre el mismo corpus textual. No se usa para predecir defectos NASA.
    vector = TfidfVectorizer(lowercase=True, strip_accents="unicode", stop_words="english",
                             ngram_range=(1, 2), max_features=1500, min_df=1 if len(df) < 30 else 2,
                             max_df=1.0, token_pattern=r"(?u)\b[\w]{2,}\b", sublinear_tf=True)
    try:
        matriz = vector.fit_transform(df["texto"])
    except ValueError as e:
        raise ValueError("Los textos no contienen vocabulario suficiente para TF-IDF.") from e
    palabras = vector.get_feature_names_out()
    pesos_prom = np.asarray(matriz.mean(axis=0)).ravel()
    top_orden = np.argsort(-pesos_prom)[:20]
    top_palabras = [(str(palabras[i]), float(pesos_prom[i])) for i in top_orden if pesos_prom[i] > 0]
    salidas = []
    conteo_entidades = Counter()
    for pos, fila in df.iterrows():
        texto = fila["texto"]
        sent = sentimiento_heuristico(texto)
        ents = extraer_entidades(texto)
        conteo_entidades.update(e["tipo"] for e in ents)
        fila_idx = len(salidas)
        vec = matriz.getrow(fila_idx)
        terminos_orden = np.argsort(-vec.data)[:5]
        terminos = [str(palabras[vec.indices[j]]) for j in terminos_orden]
        salidas.append({
            "id": fila.get("id", str(fila_idx + 1)),
            "titulo": fila["titulo"],
            "source_url": fila.get("source_url", ""),
            "sentimiento": sent["sentimiento"],
            "puntuacion_heuristica": sent["puntuacion_heuristica"],
            "terminos_sentimiento": "; ".join(sent["terminos_detectados"]),
            "terminos_tfidf": "; ".join(terminos),
            "entidades": json.dumps(ents, ensure_ascii=False),
            "resumen": resumen_individual(fila["titulo"], fila["descripcion"], sent["sentimiento"], ents),
        })
    outdf = pd.DataFrame(salidas)
    conteo_sent = Counter(outdf["sentimiento"])
    salida.mkdir(parents=True, exist_ok=True)
    outdf.to_csv(salida / "reportes_analizados.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(top_palabras, columns=["termino", "peso_tfidf_medio"]).to_csv(salida / "terminos_tfidf.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(sorted(conteo_entidades.items()), columns=["tipo_entidad", "apariciones_en_reportes"]).to_csv(salida / "entidades_resumen.csv", index=False, encoding="utf-8-sig")
    muestra = outdf.head(10)[["titulo", "sentimiento", "terminos_tfidf", "resumen"]]
    muestra.to_csv(salida / "ejemplos_analizados.csv", index=False, encoding="utf-8-sig")

    color_azul = "#1E5B91"
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    etiquetas = ["negativo", "neutral", "positivo"]
    valores = [conteo_sent[k] for k in etiquetas]
    bars = ax.bar(etiquetas, valores, color=["#245A88", "#7395B2", "#B2D6EE"])
    ax.bar_label(bars, padding=3)
    ax.set_ylabel("Reportes")
    ax.set_title("Clasificación heurística del tono")
    fig.tight_layout()
    fig.savefig(salida / "distribucion_sentimiento.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.3, 4.4))
    mejores = top_palabras[:12][::-1]
    if mejores:
        ax.barh([x for x, _ in mejores], [v for _, v in mejores], color=color_azul)
    ax.set_xlabel("Peso medio TF-IDF")
    ax.set_title("Términos destacados del corpus")
    fig.tight_layout()
    fig.savefig(salida / "terminos_tfidf.png", dpi=170)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7.5, 4.0))
    tipos = [k for k, _ in conteo_entidades.most_common(7)][::-1]
    ax.barh(tipos, [conteo_entidades[k] for k in tipos], color="#4688B8")
    ax.set_xlabel("Reportes con entidad detectada")
    ax.set_title("Entidades técnicas por tipo (reglas)")
    fig.tight_layout()
    fig.savefig(salida / "entidades.png", dpi=170)
    plt.close(fig)

    resumen = resumen_general(conteo_sent, conteo_entidades, len(df), [x for x, _ in top_palabras], origen)
    info = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "ruta_entrada": entrada.name,
        "fuente": origen,
        "ejemplo_simulado": bool(simulado),
        "filas_originales": int(inicial),
        "filas_analizadas": int(len(df)),
        "filas_excluidas_o_duplicadas": int(inicial-len(df)),
        "sentimientos": {k: int(conteo_sent[k]) for k in ["negativo", "neutral", "positivo"]},
        "entidades_por_tipo": {k: int(v) for k, v in sorted(conteo_entidades.items())},
        "tfidf_dimensiones": [int(matriz.shape[0]), int(matriz.shape[1])],
        "tfidf_top10": [{"termino": k, "peso": round(v, 6)} for k, v in top_palabras[:10]],
        "metodos": {"representacion": "TF-IDF unigramas/bigramas", "sentimiento": "lexico tecnico y negacion limitada, heuristico",
                    "entidades": "regex y diccionario técnico", "generacion": "plantillas deterministas"},
        "limitaciones": ["Tono no equivale a severidad", "Heurísticas no validadas con etiquetas humanas",
                         "NER depende de patrones conocidos", "Reportes de GitHub no tienen correspondencia individual con métricas de NASA PROMISE",
                         "Muestra de issues no necesariamente representativa"],
    }
    (salida / "reporte_pnl.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    (salida / "reporte_pnl.md").write_text(
        "# Informe de resultados PNL\n\n" +
        ("**AVISO: ESTA EJECUCIÓN UTILIZA EJEMPLOS SINTÉTICOS, NO SON REPORTES REALES.**\n\n" if simulado else "**Fuente: " + origen + " (ver enlaces por reporte en CSV).**\n\n") +
        resumen + "\n\n## Metodología\n\n1. Limpieza y tokenización.\n2. Representación TF-IDF.\n"
        "3. Polaridad de expresiones por reglas.\n4. Reconocimiento de entidades por patrones.\n"
        "5. Generación de resúmenes mediante plantillas.\n\n## Limitaciones\n\n"
        + "\n".join("- " + x for x in info["limitaciones"]) + "\n", encoding="utf-8")
    return info


def main():
    p = argparse.ArgumentParser(description="Ejecutar PNL sobre CSV de reportes técnicos")
    p.add_argument("--entrada", type=Path, default=BASE / "datos_textuales" / "reportes_github.csv")
    p.add_argument("--salida", type=Path, default=BASE / "resultados_reales")
    a = p.parse_args()
    info = analizar(a.entrada, a.salida)
    print(f"Reportes analizados: {info['filas_analizadas']}")
    print(f"Sentimientos: {info['sentimientos']}")
    print(f"Vocabulario TF-IDF: {info['tfidf_dimensiones'][1]} términos")
    print(f"Resultados: {a.salida.resolve()}")
    if info["ejemplo_simulado"]:
        print("IMPORTANTE: El análisis se hizo sobre datos SINTÉTICOS; no presentarlo como evaluación real.")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
