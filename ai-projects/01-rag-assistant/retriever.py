from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


@dataclass
class Chunk:
    id: int
    text: str
    source: str


@dataclass
class RetrievedChunk:
    text: str
    score: float
    source: str
    chunk_id: int


class SimpleRAGIndex:
    """A tiny BM25-like lexical index that requires no heavy dependencies."""

    def __init__(self, chunk_size: int = 700, overlap: int = 120):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks: List[Chunk] = []
        self.tf: List[Dict[str, int]] = []
        self.doc_len: List[int] = []
        self.df: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0

    def build(self, docs: Iterable[Tuple[str, str]]) -> None:
        self.chunks = []
        self.tf = []
        self.doc_len = []
        self.df = {}

        cid = 0
        for source, text in docs:
            for chunk_text in _split_text(text, self.chunk_size, self.overlap):
                chunk = Chunk(id=cid, text=chunk_text, source=source)
                cid += 1
                self.chunks.append(chunk)

                tokens = _tokenize(chunk_text)
                term_freq: Dict[str, int] = {}
                for t in tokens:
                    term_freq[t] = term_freq.get(t, 0) + 1

                self.tf.append(term_freq)
                self.doc_len.append(len(tokens))

                for t in term_freq.keys():
                    self.df[t] = self.df.get(t, 0) + 1

        self.avg_doc_len = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 0.0

    def search(self, query: str, k: int = 3) -> List[RetrievedChunk]:
        if not self.chunks:
            return []

        q_tokens = _tokenize(query)
        if not q_tokens:
            return []

        scores: List[Tuple[float, int]] = []
        n_docs = len(self.chunks)

        for idx, tf in enumerate(self.tf):
            score = 0.0
            dl = max(1, self.doc_len[idx])
            for term in q_tokens:
                if term not in tf:
                    continue
                df = self.df.get(term, 0)
                idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
                f = tf[term]
                k1 = 1.5
                b = 0.75
                norm = (1 - b) + b * (dl / max(1e-9, self.avg_doc_len))
                score += idf * ((f * (k1 + 1)) / (f + k1 * norm))
            if score > 0:
                scores.append((score, idx))

        scores.sort(reverse=True, key=lambda x: x[0])
        top = scores[:k]

        return [
            RetrievedChunk(
                text=self.chunks[idx].text,
                score=round(score, 4),
                source=self.chunks[idx].source,
                chunk_id=self.chunks[idx].id,
            )
            for score, idx in top
        ]

    def to_dict(self) -> dict:
        return {
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "chunks": [asdict(c) for c in self.chunks],
            "tf": self.tf,
            "doc_len": self.doc_len,
            "df": self.df,
            "avg_doc_len": self.avg_doc_len,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "SimpleRAGIndex":
        inst = cls(chunk_size=payload.get("chunk_size", 700), overlap=payload.get("overlap", 120))
        inst.chunks = [Chunk(**c) for c in payload.get("chunks", [])]
        inst.tf = [{k: int(v) for k, v in tf.items()} for tf in payload.get("tf", [])]
        inst.doc_len = [int(x) for x in payload.get("doc_len", [])]
        inst.df = {k: int(v) for k, v in payload.get("df", {}).items()}
        inst.avg_doc_len = float(payload.get("avg_doc_len", 0.0))
        return inst


def load_index(path: str | Path) -> SimpleRAGIndex:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return SimpleRAGIndex.from_dict(payload)


def retrieve_top_k(query: str, k: int = 3, index_path: str | Path = "index.json") -> List[RetrievedChunk]:
    if not Path(index_path).exists():
        return []
    idx = load_index(index_path)
    return idx.search(query, k=k)


def _tokenize(text: str) -> List[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def _split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    out: List[str] = []
    step = max(1, chunk_size - overlap)
    i = 0
    while i < len(text):
        chunk = text[i : i + chunk_size].strip()
        if chunk:
            out.append(chunk)
        if i + chunk_size >= len(text):
            break
        i += step
    return out
