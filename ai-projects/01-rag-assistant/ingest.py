from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from retriever import SimpleRAGIndex

TEXT_EXTENSIONS = {".txt", ".md", ".rst"}


def iter_documents(source_dir: Path) -> Iterable[tuple[str, str]]:
    for path in source_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if text.strip():
                yield str(path), text


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local RAG index")
    parser.add_argument("--source", default="data", help="Directory with .txt/.md/.rst files")
    parser.add_argument("--out", default="index.json", help="Output index path")
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--overlap", type=int, default=120)
    args = parser.parse_args()

    source_dir = Path(args.source)
    if not source_dir.exists():
        raise SystemExit(f"Source directory not found: {source_dir}")

    docs = list(iter_documents(source_dir))
    if not docs:
        raise SystemExit(f"No readable docs found in: {source_dir}")

    index = SimpleRAGIndex(chunk_size=args.chunk_size, overlap=args.overlap)
    index.build(docs)

    out_path = Path(args.out)
    out_path.write_text(json.dumps(index.to_dict(), ensure_ascii=False), encoding="utf-8")
    print(f"Indexed {len(index.chunks)} chunks from {len(docs)} docs -> {out_path}")


if __name__ == "__main__":
    main()
