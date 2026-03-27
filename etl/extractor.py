"""
Extrae texto plano desde archivos PDF, DOCX y TXT.
Para PDFs escaneados (sin capa de texto) aplica OCR automáticamente.
Retorna lista de dicts con {text, page, source}.
"""
import os
from pathlib import Path


def extract_txt(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return [{"text": text, "page": 1, "source": Path(file_path).name}]


def _ocr_page(page) -> str:
    """
    Aplica OCR a una página de PDF usando pytesseract.
    Requiere: pip install pytesseract pillow
    Y Tesseract instalado: https://github.com/UB-Mannheim/tesseract/wiki
    Configurar en .env: TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
    """
    try:
        import pytesseract
        from PIL import Image
        import io

        # Leer ruta de Tesseract desde .env
        tesseract_cmd = os.getenv("TESSERACT_CMD")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Intentar con español + inglés, fallback a inglés solo
        try:
            text = pytesseract.image_to_string(img, lang="spa+eng")
        except pytesseract.TesseractError:
            text = pytesseract.image_to_string(img, lang="eng")

        return text

    except ImportError:
        print("    [OCR] pytesseract o pillow no instalado.")
        print("    [OCR] Ejecutá: pip install pytesseract pillow")
        return ""
    except Exception as e:
        print(f"    [OCR] Error: {e}")
        if "tesseract" in str(e).lower() or "not found" in str(e).lower():
            print("    [OCR] Tesseract no está instalado o no se encontró.")
            print("    [OCR] Descargalo de: github.com/UB-Mannheim/tesseract/wiki")
            print("    [OCR] Luego agregá en .env: TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        return ""


def extract_pdf(file_path: str) -> list[dict]:
    import fitz  # PyMuPDF
    pages = []
    source = Path(file_path).name
    doc = fitz.open(file_path)

    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        if not text.strip():
            print(f"    Página {i} sin texto — aplicando OCR...")
            text = _ocr_page(page)
            if not text.strip():
                print(f"    Página {i} omitida (OCR no disponible o página vacía)")
        if text.strip():
            pages.append({"text": text, "page": i, "source": source})

    return pages


def extract_docx(file_path: str) -> list[dict]:
    from docx import Document
    doc = Document(file_path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [{"text": text, "page": 1, "source": Path(file_path).name}]


EXTRACTORS = {
    ".txt": extract_txt,
    ".pdf": extract_pdf,
    ".docx": extract_docx,
}


def extract(file_path: str) -> list[dict]:
    ext = Path(file_path).suffix.lower()
    if ext not in EXTRACTORS:
        raise ValueError(f"Formato no soportado: {ext}")
    return EXTRACTORS[ext](file_path)


def extract_all(docs_dir: str) -> list[dict]:
    all_pages = []
    docs_path = Path(docs_dir)
    for file in docs_path.iterdir():
        if file.suffix.lower() in EXTRACTORS:
            print(f"  Extrayendo: {file.name}")
            pages = extract(str(file))
            all_pages.extend(pages)
    return all_pages
