# MASTER PROMPT — Buscador Inteligente de Políticas Internas

## Contexto del Proyecto

Sistema RAG (Retrieval-Augmented Generation) que permite a empleados de una empresa hacer preguntas en lenguaje natural sobre políticas internas, obteniendo respuestas fundamentadas en los documentos oficiales.

---

## Stack Tecnológico

| Capa | Tecnología | Razón |
|------|-----------|-------|
| LLM | Claude API (`claude-sonnet-4-6`) | IA Generativa potente, respuestas en español |
| Embeddings | `sentence-transformers` (local) | Sin costo adicional, funciona offline |
| Vector Store | ChromaDB (persistente local) | Simple, local, sin infraestructura extra |
| ETL | PyMuPDF + python-docx + LangChain | Soporte PDF, DOCX, TXT |
| Backend | FastAPI | Rápido, async, documentación automática |
| Frontend | HTML + CSS + JS vanilla | Simple, sin dependencias, fácil de demostrar |

---

## Arquitectura RAG

```
DOCUMENTOS (PDF/DOCX/TXT)
        │
        ▼
   [ETL PIPELINE]
   ┌─────────────────────────────┐
   │ 1. Extracción de texto      │
   │ 2. Limpieza / normalización │
   │ 3. Chunking (500 tok, 50 overlap) │
   │ 4. Metadata (fuente, página)│
   └─────────────┬───────────────┘
                 │
                 ▼
   [EMBEDDINGS - sentence-transformers]
   modelo: paraphrase-multilingual-mpnet-base-v2
                 │
                 ▼
   [CHROMADB - almacenamiento vectorial local]
                 │
    ─────────────────────────────
                 │
   CONSULTA DEL USUARIO
        │
        ▼
   [RETRIEVER]
   top_k = 5 chunks más similares
   (cosine similarity)
        │
        ▼
   [PROMPT ENGINEERING]
   Sistema + Contexto recuperado + Pregunta
        │
        ▼
   [CLAUDE API]
   Genera respuesta fundamentada
        │
        ▼
   RESPUESTA + FUENTES CITADAS
```

---

## Prompt del Sistema (RAG)

```
Eres un asistente experto en políticas internas de la empresa.
Tu función es responder preguntas de los empleados basándote ÚNICAMENTE
en los documentos oficiales que se te proporcionan como contexto.

REGLAS:
1. Solo responde con información presente en el contexto proporcionado.
2. Si la información no está en los documentos, di explícitamente:
   "No encontré información sobre este tema en las políticas internas."
3. Cita siempre la fuente (nombre del documento y sección si aplica).
4. Sé claro, conciso y usa lenguaje accesible para empleados.
5. Si hay múltiples políticas relevantes, mencionas todas.
6. No inventes, no asumas, no extrapoles más allá del contexto.

CONTEXTO DE DOCUMENTOS:
{context}

PREGUNTA DEL EMPLEADO:
{question}

RESPUESTA:
```

---

## ETL — Normalización de Datos

### Flujo de Ingesta
```
Archivo → Extracción → Limpieza → Chunking → Embedding → ChromaDB
```

### Reglas de Limpieza
- Eliminar caracteres especiales no semánticos (`\x00`, tabs múltiples)
- Normalizar espacios y saltos de línea
- Eliminar headers/footers repetitivos (número de página, nombre empresa)
- Conservar estructura: títulos, numeraciones, listas

### Estrategia de Chunking
- Tamaño: **500 tokens** por chunk
- Overlap: **50 tokens** (para no perder contexto entre chunks)
- Split por: párrafo > oración > token
- Metadata por chunk:
  - `source`: nombre del archivo
  - `page`: número de página (si aplica)
  - `chunk_id`: identificador único
  - `doc_type`: tipo de política (RRHH, TI, Finanzas, etc.)

---

## Criterios de Evaluación — Plan de Ataque

### 1. Uso de IA Generativa ✅
- Claude API como LLM principal
- Prompt engineering con instrucciones estrictas de grounding
- Respuestas en lenguaje natural, contextualizadas

### 2. Uso de RAG ✅
- Pipeline completo: ingest → embed → store → retrieve → generate
- Retrieval semántico (no keyword search)
- Contexto inyectado al prompt con chunks relevantes
- Citación de fuentes en la respuesta

### 3. Calidad de Respuesta ✅
- El modelo solo responde con info del corpus
- Se muestra score de similitud de los chunks recuperados
- Respuesta incluye fuente y página
- Manejo explícito de "no encontrado"

### 4. Demo ✅
- Interfaz web limpia con chat
- Panel lateral con documentos cargados
- Visualización de fuentes usadas en cada respuesta
- Script de demo con preguntas de ejemplo

### 5. Datos / ETL ✅
- Pipeline modular y reutilizable
- Soporte multi-formato (PDF, DOCX, TXT)
- Logs de ingesta (qué se procesó, cuántos chunks)
- Documentos de ejemplo de políticas internas

---

## Estructura del Proyecto

```
IA GENERATIVA - PROYECTO 2/
├── MASTER_PROMPT.md          ← Este archivo
├── README.md                 ← Guía de instalación y uso
├── requirements.txt          ← Dependencias Python
├── .env.example              ← Variables de entorno
│
├── docs/                     ← Documentos de políticas (input)
│   ├── politica_vacaciones.txt
│   ├── politica_home_office.txt
│   ├── politica_uso_tecnologia.txt
│   ├── politica_gastos_viaje.txt
│   └── codigo_conducta.txt
│
├── etl/                      ← Pipeline de ingesta
│   ├── __init__.py
│   ├── extractor.py          ← Extrae texto de PDF/DOCX/TXT
│   ├── cleaner.py            ← Limpieza y normalización
│   ├── chunker.py            ← Divide en chunks con overlap
│   └── ingest.py             ← Orquesta el pipeline ETL completo
│
├── rag/                      ← Motor RAG
│   ├── __init__.py
│   ├── embedder.py           ← Genera embeddings
│   ├── vectorstore.py        ← Interacción con ChromaDB
│   ├── retriever.py          ← Búsqueda semántica
│   └── generator.py          ← Llama a Claude API con contexto
│
├── api/                      ← Backend FastAPI
│   ├── __init__.py
│   ├── main.py               ← App principal + endpoints
│   ├── models.py             ← Schemas Pydantic
│   └── routes/
│       ├── chat.py           ← POST /api/chat
│       └── documents.py      ← GET /api/documents
│
├── frontend/                 ← Interfaz web
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── vectorstore/              ← ChromaDB persistente (generado)
│
└── scripts/
    ├── run_etl.py            ← Ejecuta ingesta de documentos
    └── demo_questions.py     ← Script de demo con preguntas ejemplo
```

---

## Plan de Desarrollo (orden de implementación)

1. `docs/` — Crear documentos de políticas de ejemplo
2. `etl/` — Pipeline de extracción, limpieza y chunking
3. `rag/embedder.py` + `rag/vectorstore.py` — Almacenamiento vectorial
4. `rag/retriever.py` + `rag/generator.py` — Motor RAG
5. `api/` — Backend FastAPI
6. `frontend/` — Interfaz web
7. `scripts/` — Scripts de demo y utilidades
8. `README.md` — Documentación final

---

## Variables de Entorno Requeridas

```env
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
CHROMA_PATH=./vectorstore
DOCS_PATH=./docs
TOP_K_RESULTS=5
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```
