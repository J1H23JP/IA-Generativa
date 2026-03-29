import os
from dotenv import load_dotenv
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader

load_dotenv()

def test_conexion():
    endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
    key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
    pdf_path = "docs/REGLAMENTO-INTERNO-DE-TRABAJO-DE-LA-UNIVERSIDAD-DE-CUENCA-APROBACION-14022014.pdf"

    print(f"Iniciando OCR con Azure para: {pdf_path}")
    try:
        loader = AzureAIDocumentIntelligenceLoader(
            api_endpoint=endpoint, 
            api_key=key, 
            file_path=pdf_path, 
            api_model="prebuilt-layout",
            mode="page"

        )
        documentos = loader.load()
        print(f"Procesamiento exitoso. Páginas detectadas: {len(documentos)}")
        # Verificamos si realmente extrajo texto de las imágenes
        texto_total = sum(len(doc.page_content) for doc in documentos)
        print(f"Total de caracteres extraídos (OCR): {texto_total}")
        
        if len(documentos) > 0:
            print("\nPrimeras palabras de la página 1:")
            print(documentos[0].page_content[:150])
    except Exception as e:
        print(f"Error detectado: {e}")

if __name__ == "__main__":
    test_conexion()