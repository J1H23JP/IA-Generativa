# Buscador Inteligente de Políticas Internas

Sistema RAG (Retrieval-Augmented Generation) que permite a empleados consultar las políticas internas de la empresa en lenguaje natural, obteniendo respuestas fundamentadas en los documentos oficiales.

## Stack

- **LLM**: Claude API (`claude-sonnet-4-6`)
- **Embeddings**: `sentence-transformers` — modelo multilingüe (local, sin costo)
- **Vector Store**: ChromaDB (persistente local)
- **Backend**: FastAPI
- **Frontend**: HTML + CSS + JS vanilla

## Estructura

```
IA GENERATIVA - PROYECTO 2/
├── docs/          → Documentos de políticas (PDF, DOCX, TXT)
├── etl/           → Pipeline ETL: extracción, limpieza, chunking
├── rag/           → Motor RAG: embeddings, vectorstore, retriever, generator
├── api/           → Backend FastAPI
├── frontend/      → Interfaz web
├── scripts/       → ETL runner y demo
└── vectorstore/   → ChromaDB local (generado al correr ETL)
```

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env
# Editar .env y agregar tu ANTHROPIC_API_KEY
```

## Uso

### Paso 1 — Indexar documentos

Colocá tus documentos (PDF, DOCX o TXT) en la carpeta `docs/` y ejecutá:

```bash
python scripts/run_etl.py
```

Para re-indexar desde cero:
```bash
python scripts/run_etl.py --reset
```

### Paso 2 — Iniciar el servidor

```bash
uvicorn api.main:app --reload --port 8000
```

Abrí el navegador en: **http://localhost:8000**

### Demo por consola

```bash
python scripts/demo_questions.py
```

## API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/chat` | Hacer una consulta |
| GET | `/api/documents` | Listar documentos indexados |
| GET | `/api/status` | Estado del sistema |
| GET | `/docs` | Swagger UI (documentación automática) |

### Ejemplo de consulta

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuántos días de vacaciones me corresponden?", "top_k": 5}'
```
