from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from config import settings
from retriever import retrieve_top_k


app = FastAPI(title="RAG Assistant", version="0.3.0")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    k: int = Field(default=3, ge=1, le=10)


def _verify_token(auth_header: str | None) -> None:
    if not settings.api_token:
        return
    expected = f"Bearer {settings.api_token}"
    if auth_header != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health():
    return {"ok": True, "index_path": settings.index_path}


@app.post("/ask")
def ask(req: AskRequest, authorization: str | None = Header(default=None)):
    _verify_token(authorization)
    chunks = retrieve_top_k(req.question, k=req.k, index_path=settings.index_path)
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
