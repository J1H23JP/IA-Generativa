"""
Extrae texto plano desde archivos PDF, DOCX y TXT.
Para PDFs escaneados (sin capa de texto) aplica OCR automáticamente.
Retorna lista de dicts con {text, page, source}.
"""
from pathlib import Path


def extract_txt(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return [{"text": text, "page": 1, "source": Path(file_path).name}]


def _ocr_page(page) -> str:
    """
    Aplica OCR a una página de PDF usando pytesseract.
    Requiere: pip install pytesseract pillow
    Y Tesseract instalado en el sistema con paquete de idioma español.
    """
    try:
        import pytesseract
        from PIL import Image
        import io
        pix = page.get_pixmap(dpi=200)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang="spa+eng")
    except ImportError:
        print("    [AVISO] pytesseract/pillow no instalado. Página omitida.")
        return ""
    except Exception as e:
        print(f"    [AVISO] OCR falló: {e}")
        return ""


def extract_pdf(file_path: str) -> list[dict]:
    import fitz  # PyMuPDF
    pages = []
    doc = fitz.open(file_path)
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        if not text.strip():
            print(f"    Página {i} sin texto — aplicando OCR...")
            text = _ocr_page(page)
        if text.strip():
            pages.append({"text": text, "page": i, "source": Path(file_path).name})
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
    """Extrae texto de todos los documentos en un directorio."""
    all_pages = []
    docs_path = Path(docs_dir)
    for file in docs_path.iterdir():
        if file.suffix.lower() in EXTRACTORS:
            print(f"  Extrayendo: {file.name}")
            pages = extract(str(file))
            all_pages.extend(pages)
    return all_pages
