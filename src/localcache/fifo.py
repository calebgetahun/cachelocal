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

    def _add_to_front(self, node: DLLNode[K, V]) -> None:
        """Insert node at front of list after head node"""
        if node.prev is not None or node.next is not None:
            raise RuntimeError("Attempting to add a node that already contains linkages")
        
        node.next = self.head.next
        node.prev = self.head

        self.head.next.prev = node
        self.head.next = node
    
    def _remove(self, node: DLLNode[K, V]) -> None:
        """Remove node from list"""
        if node is self.head or node is self.tail:
            return
        
        if node.prev is None or node.next is None:
            raise RuntimeError("Attempting to remove a detached node")
        
        prev = node.prev
        nxt = node.next
        prev.next = nxt
        nxt.prev = prev

        node.prev = None
        node.next = None
    
    def _delete_node(self, key: K, node: DLLNode[K, V]) -> None:
        """
        deletes a node from the cache and DLL
        """
        self._remove(node)
        if key in self.cache:
            self.cache.pop(key, None)

    def _is_expired(self, node: DLLNode[K, V], now: Optional[float] = None) -> bool:
        """
        Check if node is expired given the ttl it currently holds
        """
        if node.expires_at is None:
            return False
        if now is None:
            now = time.monotonic()
        return now >= node.expires_at

    def _evict_one(self, now: float) -> None:
        curr = self.tail.prev

        while curr is not None and curr is not self.head:
            if self._is_expired(curr, now):
                assert curr.key is not None
                self._delete_node(curr.key, curr)
                return
            curr = curr.prev

        oldest = self.tail.prev
        if oldest is not None and oldest is not self.head:
            self._remove(oldest)
            if oldest.key is not None:
                self.cache.pop(oldest.key, None)
    
    def get(self, key: K) -> Optional[V]:
        """
        Return value associated with key if exists within cache and not expired, None otherwise.
        """
        with self._lock:
            node = self.cache.get(key)

            if node is None:
                if self._track_stats:
                    self._stats.misses += 1
                return None
            
            now = time.monotonic()

            if self._is_expired(node, now):
                self._delete_node(key, node)
                if self._track_stats:
                    self._stats.misses += 1
                return None

            if self._track_stats:
                self._stats.hits += 1
            return node.val

    def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        """
        ttl is in seconds. If ttl is None, entry has no expiration.
        """
        with self._lock:
            now = time.monotonic()
            node = self.cache.get(key)
            expiration_time = (now + ttl_seconds) if ttl_seconds is not None else None

            if node is not None:
                node.val = value
                node.expires_at = expiration_time
                return

            new_node: DLLNode[K, V] = DLLNode(key=key, val=value, expires_at=expiration_time)
            self._add_to_front(new_node)
            self.cache[key] = new_node

            if len(self.cache) > self.capacity:
                self._evict_one(now)
                if self._track_stats:
                    self._stats.evictions += 1

    def delete(self, key: K) -> bool:
        """
        Return True if key existed and was removed, False otherwise.
        """
        with self._lock:
            node = self.cache.get(key)
            if node is None:
                return False

            self._delete_node(key, node)
            return True

    def clear(self) -> None:
        """
        Remove all entries from the cache.
        """
        with self._lock:
            self.cache.clear()
            self.head.next = self.tail
            self.tail.prev = self.head

            if self._track_stats:
                self._stats = CacheStats()

    def __len__(self) -> int:
        """
        Returns number of entries in cache
        """
        with self._lock:
            return len(self.cache)
        
    def get_stats(self) -> CacheStats:
        if not self._track_stats:
            return CacheStats()
        
        return CacheStats(
            hits=self._stats.hits,
            misses=self._stats.misses,
            evictions=self._stats.evictions
        )
