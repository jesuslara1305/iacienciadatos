"""PNL académico de reportes de defectos. Independiente del modelo NASA PROMISE.

Técnicas: limpieza/tokenización, TF-IDF, polaridad heurística técnica,
extracción de entidades mediante reglas y generación de resúmenes de plantilla.
No es un modelo de lenguaje ni un estimador de severidad.
"""
from __future__ import annotations

import html
import re
import unicodedata
from collections import Counter
from typing import Any

# Los reportes de GitHub son principalmente en inglés; las expresiones en español
# se incluyen para probar entradas manuales. No hay detección automática de idioma.
LEXICO_NEGATIVO = {
    "crash": 3, "crashes": 3, "crashed": 3, "crashing": 3,
    "fail": 2, "failed": 2, "fails": 2, "failing": 2,
    "error": 2, "errors": 2, "exception": 2, "bug": 1,
    "broken": 2, "freeze": 2, "frozen": 2, "hang": 2,
    "slow": 1, "unusable": 3, "missing": 1, "timeout": 2,
    "corrupt": 3, "corrupted": 3, "incorrect": 2, "wrong": 2,
    "failsafe": 1, "regression": 2, "failure": 2,
    "bloqueo": 2, "bloquea": 2, "fallo": 2, "falla": 2,
    "falla": 2, "error": 2, "lento": 1, "imposible": 2,
}
LEXICO_POSITIVO = {
    "fixed": 2, "fixes": 1, "resolved": 3, "working": 1,
    "works": 2, "success": 3, "successful": 3, "stable": 2,
    "improved": 2, "great": 2, "perfect": 2, "passed": 2,
    "restored": 2, "solucionado": 3, "funciona": 2,
    "corregido": 2, "estable": 2, "exitoso": 3,
}
NEGACIONES = {"not", "no", "never", "cannot", "cant", "can't", "doesnt", "doesn't", "isnt", "isn't", "sin"}

TECH = {
    "SISTEMA_OPERATIVO": ["windows", "linux", "ubuntu", "macos", "android", "ios", "debian", "fedora"],
    "TECNOLOGIA": ["python", "javascript", "typescript", "java", "docker", "node.js", "nodejs", "react", "angular", "electron", "vscode", "visual studio code", "postgresql", "mysql", "git", "kubernetes"],
    "COMPONENTE": ["terminal", "editor", "extension", "extensions", "debugger", "api", "compiler", "parser", "database", "authentication", "login", "file explorer", "settings", "sidebar", "notebook", "kernel"],
}

TOKEN_RX = re.compile(r"[\wáéíóúüñ]+(?:[.-][\wáéíóúüñ]+)*", flags=re.I | re.U)
VERSION_RX = re.compile(r"(?<![\w.])v?\d+\.\d+(?:\.\d+)?(?:[-_](?:rc|beta|alpha)\d*)?(?![\w.])", re.I)
ERROR_RX = re.compile(r"\b(?:HTTP\s*[45]\d\d|(?:ERR|E|ERROR)[-_ ]?\d{2,6}|0x[0-9a-f]{4,8}|[45]\d\d\s+(?:error|status))\b", re.I)
FILE_RX = re.compile(r"\b[\w][\w.\-]{0,70}\.(?:py|js|ts|tsx|jsx|json|yml|yaml|html|css|java|cpp|c|h|md|xml|sql|ipynb|csv|exe|dll|log)\b", re.I)
EMAIL_RX = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
SECRET_RX = re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")


def anonimizar(texto: str) -> str:
    texto = SECRET_RX.sub("[TOKEN_OCULTO]", texto)
    return EMAIL_RX.sub("[CORREO_OCULTO]", texto)


def limpiar_texto(texto: Any) -> str:
    """Quita marcado y ruido sin eliminar nombres técnicos, versiones ni errores."""
    if texto is None:
        return ""
    t = unicodedata.normalize("NFKC", str(texto))
    t = html.unescape(t)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"!\[([^]]*)\]\([^)]*\)", r" \1 ", t)
    t = re.sub(r"\[([^]]+)\]\([^)]*\)", r" \1 ", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"\s+", " ", anonimizar(t))
    return t.strip()


def tokens(texto: str) -> list[str]:
    return [w.lower() for w in TOKEN_RX.findall(texto)]


def sentimiento_heuristico(texto: str) -> dict[str, Any]:
    """Polaridad de expresiones técnicas con negación local; NO severidad ni exactitud validada."""
    seq = tokens(texto)
    score = 0
    evidencias: list[str] = []
    for i, w in enumerate(seq):
        peso = LEXICO_POSITIVO.get(w, 0) - LEXICO_NEGATIVO.get(w, 0)
        if peso == 0:
            continue
        antes = seq[max(0, i - 2):i]
        if any(x in NEGACIONES for x in antes):
            peso = -peso
        score += peso
        evidencias.append(w)
    if score <= -2:
        etiqueta = "negativo"
    elif score >= 2:
        etiqueta = "positivo"
    else:
        etiqueta = "neutral"
    return {"sentimiento": etiqueta, "puntuacion_heuristica": int(score), "terminos_detectados": sorted(set(evidencias))}


def extraer_entidades(texto: str) -> list[dict[str, str]]:
    """Reconocimiento de entidades técnicas por reglas; no requiere modelos descargados."""
    salida: dict[tuple[str, str], dict[str, str]] = {}
    for tipo, palabras in TECH.items():
        for palabra in sorted(palabras, key=len, reverse=True):
            rx = re.compile(r"(?<![\w])" + re.escape(palabra) + r"(?![\w])", re.I)
            for m in rx.finditer(texto):
                clave = (tipo, m.group().lower())
                salida[clave] = {"tipo": tipo, "valor": m.group()}
    for tipo, rx in [("VERSION", VERSION_RX), ("CODIGO_ERROR", ERROR_RX), ("ARCHIVO", FILE_RX)]:
        for m in rx.finditer(texto):
            clave = (tipo, m.group().lower())
            salida[clave] = {"tipo": tipo, "valor": m.group()}
    return sorted(salida.values(), key=lambda x: (x["tipo"], x["valor"].lower()))


def resumen_individual(titulo: str, cuerpo: str, sentimiento: str, entidades: list[dict[str, str]]) -> str:
    # Generación mediante plantilla, NO modelo generativo.
    t = limpiar_texto(titulo)
    frase = (t[:155].rstrip(" .") + ("..." if len(t) > 155 else "")) if t else "Reporte sin título"
    tipos = Counter(e["tipo"] for e in entidades)
    detalle = ", ".join(f"{tipo.lower().replace('_', ' ')} ({n})" for tipo, n in tipos.most_common(3))
    return f"Incidencia: {frase}. Tono estimado por reglas: {sentimiento}. Entidades técnicas detectadas: {detalle or 'ninguna'}."


def resumen_general(sentimientos: Counter, entidades: Counter, registros: int, top_terminos: list[str], fuente: str) -> str:
    frecuentes = ", ".join(top_terminos[:5]) or "sin términos suficientemente frecuentes"
    entidades_texto = ", ".join(f"{k} ({v})" for k, v in entidades.most_common(3)) or "no identificadas"
    return (f"Se analizaron {registros} reportes ({fuente}). La clasificación heurística del tono fue: "
            f"negativo {sentimientos.get('negativo', 0)}, neutral {sentimientos.get('neutral', 0)} y "
            f"positivo {sentimientos.get('positivo', 0)}. Los términos TF-IDF destacados fueron: "
            f"{frecuentes}. Las categorías de entidades más frecuentes: {entidades_texto}. "
            "Estas estadísticas describen el texto; no son predicciones de defectos NASA ni medidas de severidad.")
