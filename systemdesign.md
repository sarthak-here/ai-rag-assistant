# AI RAG Assistant — System Design

## What It Does
A production-ready RAG (Retrieval-Augmented Generation) assistant with a FastAPI backend, ChromaDB vector store, rate limiting, evaluation harness, and Docker support. Ingest your documents, then query them through a REST API or test suite.

---

## Architecture

```
Client (HTTP)
      |
      v
+---------------------------------------------------+
|              api.py  (FastAPI)                    |
|  POST /ingest   -> trigger document ingestion     |
|  POST /query    -> retrieve + generate answer     |
|  GET  /health   -> liveness check                 |
|      |                                            |
|  rate_limit.py  (per-IP token bucket)             |
+---------------------------------------------------+
      |              |
      v              v
 ingest.py       retriever.py
      |              |
      v              v
 ChromaDB     ChromaDB.query()
 (vector       + LLM call
  store)       (OpenAI or local)
      |
      v
 data.sample/  (source documents)
```

---

## Input

| Endpoint | Input | Detail |
|---|---|---|
| POST /ingest | directory path | Load, chunk, embed, store in ChromaDB |
| POST /query | {"question": "...", "k": 5} | Return answer + source chunks |
| eval.py | sample_cases.jsonl | Batch evaluation against ground truth |

---

## Data Flow

```
INGEST:
  POST /ingest {"path": "./data"}
        |
  ingest.py:
  - Recursively load .md, .txt, .pdf files
  - Chunk: RecursiveCharacterTextSplitter
  - Embed: OpenAI text-embedding-3-small
  - Store: ChromaDB collection (persistent)

QUERY:
  POST /query {"question": "What is the refund policy?"}
        |
  rate_limit.py: check IP request count (token bucket)
        |
  retriever.py:
  - Embed question
  - ChromaDB.query(k=5) -> top-5 chunks + metadata
  - Build prompt: [system] + [chunks] + [question]
  - OpenAI ChatCompletion (gpt-4o)
  - Return: {answer, sources[{text, doc, score}]}

EVAL:
  eval.py reads sample_cases.jsonl
  For each case: run /query, compare to expected answer
  Score: exact match + LLM-as-judge (GPT grades the answer)
  Output: accuracy, avg_latency, failure_cases
```

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| FastAPI | Async, OpenAPI docs auto-generated, production-grade |
| Rate limiting (rate_limit.py) | Prevents abuse and runaway OpenAI costs |
| Docker support | Reproducible deployment; ChromaDB and app in same container |
| eval.py with LLM-as-judge | Traditional exact match fails for open-ended answers; LLM grading is more meaningful |
| Source chunk return in response | Users can verify which document drove the answer |

---

## Interview Conclusion

This is the most production-hardened RAG project in the portfolio. The inclusion of rate limiting, Docker, CI (GitHub Actions workflow), and an evaluation harness separates it from a prototype. The evaluation design is particularly noteworthy: sample_cases.jsonl contains question-answer pairs, and eval.py runs the full pipeline against them, using GPT as a judge to score open-ended answers — which is the industry standard for RAG evaluation (used by teams at OpenAI and Anthropic). The rate limiter is a token bucket implementation that prevents a single client from draining the OpenAI quota. If I were taking this to production, I would add a feedback endpoint (thumbs up/down per answer) to continuously fine-tune the retrieval parameters, and replace the single ChromaDB collection with namespaced collections per user or document set.
