from __future__ import annotations
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")

@dataclass
class DLLNode(Generic[K, V]):
    key: Optional[K] = None
    val: Optional[V] = None
    prev: Optional["DLLNode[K, V]"] = None
    next: Optional["DLLNode[K, V]"] = None
    expires_at: Optional[float] = None  # monotonic timestamp