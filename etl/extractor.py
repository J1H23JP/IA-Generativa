"""
Extrae texto plano desde archivos PDF, DOCX y TXT.
Para PDFs utiliza Azure AI Document Intelligence, procesando texto nativo y OCR en la nube.
Retorna lista de dicts con {text, page, source}.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def extract_txt(file_path: str) -> list[dict]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return [{"text": text, "page": 1, "source": Path(file_path).name}]

def extract_pdf_con_azure(file_path: str) -> list[dict]:
    """
    Utiliza el modelo prebuilt-layout de Azure para extraer texto, 
    tablas y aplicar OCR automáticamente a documentos escaneados.
    """
    from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
    
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

    if not endpoint or not key:
        raise ValueError("Faltan las credenciales de Azure en el archivo .env")

    print(f"    [Azure AI] Procesando documento: {Path(file_path).name}")
    
    loader = AzureAIDocumentIntelligenceLoader(
        api_endpoint=endpoint, 
        api_key=key, 
        file_path=file_path, 
        api_model="prebuilt-layout",
        mode="page"
    )
    
    # Langchain devuelve una lista de objetos Document
    docs_azure = loader.load()
    
    pages = []
    source = Path(file_path).name
    
    # Asignamos el texto y calculamos el número de página
    for i, doc in enumerate(docs_azure, start=1):
        texto = doc.page_content
        if texto.strip():
            pages.append({"text": texto, "page": i, "source": source})
    return pages

def extract_docx(file_path: str) -> list[dict]:
    from docx import Document
    doc = Document(file_path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return [{"text": text, "page": 1, "source": Path(file_path).name}]

EXTRACTORS = {
    ".txt": extract_txt,
    ".pdf": extract_pdf_con_azure, # Apunta a la nueva función
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