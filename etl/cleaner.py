"""
Limpieza y normalización de texto extraído de documentos.
"""
import re


def clean(text: str) -> str:
    # Eliminar caracteres nulos y de control
    text = text.replace("\x00", "").replace("\r", "\n")

    # Normalizar saltos de línea múltiples (máximo 2 consecutivos)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Eliminar espacios múltiples dentro de una línea
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Eliminar líneas que solo tienen números (páginas de PDF)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

    # Eliminar guiones de separación decorativos (---, ===, etc.)
    text = re.sub(r"^[-=_*]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Eliminar espacios al inicio/fin de cada línea
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Trim final
    return text.strip()


def clean_pages(pages: list[dict]) -> list[dict]:
    """Aplica limpieza a cada página extraída."""
    cleaned = []
    for page in pages:
        clean_text = clean(page["text"])
        if len(clean_text) > 50:  # Descartar páginas casi vacías
            cleaned.append({**page, "text": clean_text})
    return cleaned
