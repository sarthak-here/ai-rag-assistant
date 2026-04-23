# AI RAG Assistant - System Design

## What It Does
A production-ready RAG assistant with a FastAPI backend, ChromaDB vector store, rate
limiting, evaluation harness, and Docker support. Ingest documents, then query them
through a REST API with source citations.

---

## Architecture

```
Client (HTTP)
      |
      v
+---------------------------------------------------+
|              api.py (FastAPI)                     |
|  POST /ingest -> trigger document ingestion       |
|  POST /query  -> retrieve + generate answer       |
|  GET  /health -> liveness check                   |
|      |                                            |
|  rate_limit.py (per-IP token bucket)              |
+---------------------------------------------------+
      |              |
      v              v
 ingest.py       retriever.py
      |              |
      v              v
 ChromaDB        ChromaDB.query()
 vector store    + LLM call
      |
 data.sample/ (source documents)
```

---

## Data Flow

```
INGEST:
  POST /ingest {"path": "./data"}
  -> ingest.py:
     Load .md, .txt, .pdf files
     RecursiveCharacterTextSplitter
     Embed: OpenAI text-embedding-3-small
     Store: ChromaDB collection (persistent)

QUERY:
  POST /query {"question": "What is the refund policy?"}
  -> rate_limit.py: check per-IP request count (token bucket)
  -> retriever.py:
     Embed question -> ChromaDB.query(k=5) -> top-5 chunks
     Prompt: [system] + [chunks] + [question]
     OpenAI ChatCompletion (gpt-4o)
     Return: {answer, sources[{text, doc, score}]}

EVAL (eval.py):
  Read sample_cases.jsonl
  For each case: POST /query, compare to expected
  Score: exact match + LLM-as-judge (GPT grades answer)
  Output: accuracy, avg_latency, failure_cases
```

---

## Key Design Decisions

| Decision                       | Reason                                            |
|--------------------------------|---------------------------------------------------|
| FastAPI                        | Async, auto-generates OpenAPI docs                |
| Rate limiting (token bucket)   | Prevents abuse and runaway OpenAI API costs       |
| Docker support                 | Reproducible deployment, consistent environment   |
| LLM-as-judge in eval.py        | Exact match fails for open-ended answers          |
| Source chunk citations         | Users verify which document drove each answer     |

---

## Interview Conclusion

This is the most production-hardened RAG project in the portfolio. Rate limiting, Docker,
CI (GitHub Actions), and an evaluation harness separate it from a prototype. The eval
design is noteworthy: sample_cases.jsonl has question-answer pairs, and eval.py runs
the full pipeline against them using GPT as a judge -- the industry standard for RAG
evaluation. The token bucket rate limiter prevents a single client from draining the
OpenAI quota. Production next steps: add a feedback endpoint (thumbs up/down) for
continuous retrieval tuning, and namespace ChromaDB collections per user or document set.
