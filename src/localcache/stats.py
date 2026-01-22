from __future__ import annotations
from dataclasses import dataclass

@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0