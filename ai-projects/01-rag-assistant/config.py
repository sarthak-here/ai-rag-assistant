from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    index_path: str = os.getenv("RAG_INDEX_PATH", "index.json")
    api_token: str = os.getenv("RAG_API_TOKEN", "")
    rate_limit_per_minute: int = int(os.getenv("RAG_RATE_LIMIT_PER_MINUTE", "60"))


settings = Settings()
