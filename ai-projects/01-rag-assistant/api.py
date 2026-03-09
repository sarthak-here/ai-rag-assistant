from __future__ import annotations

import os
from fastapi import FastAPI
from pydantic import BaseModel, Field

from retriever import retrieve_top_k


INDEX_PATH = os.getenv("RAG_INDEX_PATH", "index.json")

app = FastAPI(title="RAG Assistant", version="0.2.0")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    k: int = Field(default=3, ge=1, le=10)


@app.get("/health")
def health():
    return {"ok": True, "index_path": INDEX_PATH}


@app.post("/ask")
def ask(req: AskRequest):
    chunks = retrieve_top_k(req.question, k=req.k, index_path=INDEX_PATH)
    sources = [
        {
            "text": c.text,
            "score": c.score,
            "source": c.source,
            "chunk_id": c.chunk_id,
        }
        for c in chunks
    ]

    if not sources:
        answer = "No relevant context found. Please ingest documents first."
    else:
        answer = "\n".join(
            [
                "Answer grounded on retrieved documents:",
                f"Top context: {sources[0]['text'][:300]}",
                f"Retrieved {len(sources)} chunk(s).",
            ]
        )

    return {"question": req.question, "answer": answer, "sources": sources}
