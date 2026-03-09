from __future__ import annotations

import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        window_start = now - 60.0
        q = self.hits[key]

        while q and q[0] < window_start:
            q.popleft()

        if len(q) >= self.max_requests:
            return False

        q.append(now)
        return True
