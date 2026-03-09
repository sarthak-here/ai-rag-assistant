# 01 — RAG Assistant

[![CI](https://github.com/sarthak-here/ai-rag-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/sarthak-here/ai-rag-assistant/actions/workflows/ci.yml)

A lightweight Retrieval-Augmented Generation (RAG) starter project.

## Features
- FastAPI service with `/ask` and `/health`
- Local ingestion from `data/` (`.txt`, `.md`, `.rst`)
- Small BM25-like retriever (no vector DB required)
- JSON index output (`index.json`)

## Project Structure
- `ingest.py` — build index from local documents
- `retriever.py` — indexing + retrieval logic
- `api.py` — FastAPI inference endpoint
- `requirements.txt` — dependencies

## Quickstart
```bash
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 1) Add source docs
Create a `data/` folder and put files such as:
- `data/faq.md`
- `data/product_notes.txt`

### 2) Build index
```bash
python ingest.py --source data --out index.json
```

### 3) Run API
```bash
uvicorn api:app --reload --port 8000
```

### 4) Ask
```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this assistant for?","k":3}'
```

## Environment
- `RAG_INDEX_PATH` (default: `index.json`)

## Development
```bash
make install
make test
```

## Notes for public release
- Add sample dataset + benchmark script
- Add optional semantic embedding backend (FAISS/Chroma)
- Add auth/rate-limits for hosted deployments
