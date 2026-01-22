from __future__ import annotations
import time
from threading import Lock
from typing import Dict, Hashable, Optional, TypeVar

from .base import Cache
from .dll import DLLNode
from .stats import CacheStats

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

class FIFOCache(Cache[K, V]):
    """
    Simple in-memory FIFO cache with O(1) get/set.

    Doubly linked list + hashmap implementation

    Thread-safe via a single lock guarding the hashmap and linked list.
    """
    def __init__(self, capacity: int, track_stats: bool = False):
        if capacity <= 0:
            raise ValueError("FIFOCache capacity must be > 0")
        self.capacity = capacity
        self.cache: Dict[K, DLLNode[K, V]] = {}

        self.head = DLLNode()
        self.tail = DLLNode()

        self.head.next = self.tail
        self.tail.prev = self.head

        self._lock = Lock()
        self._track_stats = track_stats
        self._stats = CacheStats() if track_stats else None
        
    def get_stats(self) -> CacheStats:
        if not self._track_stats:
            return CacheStats()
        
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            evictions=self._stats.evictions
        )
