from __future__ import annotations
from collections import defaultdict
import time
from threading import Lock
from typing import Dict, Hashable, Optional, TypeVar

from .base import Cache
from .dll import DLLNode, DLList
from .stats import CacheStats

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

class LFUCache(Cache[K, V]):
    """
    Simple in-memory LFU cache with O(1) get/set.

    Uses frequency buckets (each bucket is a doubly-linked list) + hashmap.
    Evicts least frequently used entries. Ties broken by LRU within same frequency.

    Thread-safe via a single lock guarding all data structures.
    """
    def __init__(self, capacity: int, track_stats: bool = False):
        if capacity <= 0:
            raise ValueError("LFUCache capacity must be > 0")
        
        self.capacity = capacity

        self.cache: Dict[K, DLLNode[K, V]] = {}
        self.node_freq: Dict[K, int] = {}
        self.freq_lists: defaultdict[int, DLList[K, V]] = defaultdict(DLList)
        self.min_freq = 1

        self._lock = Lock()
        self._track_stats = track_stats
        self._stats = CacheStats() if track_stats else None

    def _is_expired(self, node: DLLNode[K, V], now: Optional[float] = None) -> bool:
        """
        Check if node is expired given the ttl it currently holds
        """
        if node.expires_at is None:
            return False
        if now is None:
            now = time.monotonic()
        return now >= node.expires_at
    
    def _delete_node(self, key: K) -> None:
        """
        deletes a node from the cache and DLL
        """
        if key in self.cache:
            node = self.cache.pop(key)
            freq = self.node_freq.pop(key)
            self.freq_lists[freq].unlink_node(node)

            if self.freq_lists[self.min_freq].is_empty():
                self.min_freq += 1

    def _update_freq_lists(self, key: K, node: DLLNode[K, V]) -> None:
        freq = self.node_freq[key]
        self.freq_lists[freq].unlink_node(node)
        self.freq_lists[freq + 1].add_to_front(node)
        self.node_freq[key] += 1

        if self.freq_lists[self.min_freq].is_empty():
            self.min_freq += 1

    def _evict_one(self, now: float) -> None:
        #remove oldest from self.freq_list[self.min_freq] DLList
        while self.min_freq in self.freq_lists:
            node = self.freq_lists[self.min_freq].pop_tail()

            if node is None:
                self.min_freq += 1
            else:
                self.cache.pop(node.key)
                self.node_freq.pop(node.key)

                if not self._is_expired(node, now):
                    if self._track_stats:
                        self._stats.evictions += 1
                    return

    def get(self, key: K) -> Optional[V]:
        with self._lock:
            node = self.cache.get(key)

            if node is None:
                if self._track_stats:
                    self._stats.misses += 1
                return None
            
            curr_time = time.monotonic()

            if self._is_expired(node, curr_time):
                self._delete_node(key)
                if self._track_stats:
                    self._stats.misses += 1
                return None

            self._update_freq_lists(key, node)
            
            if self._track_stats:
                self._stats.hits += 1
            return node.val

    def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        with self._lock:
            now = time.monotonic()
            node = self.cache.get(key)
            expiration_time = (now + ttl_seconds) if ttl_seconds is not None else None

            if node is not None:
                if self._is_expired(node, now):
                    self._delete_node(key)

                else:
                    node.val = value
                    node.expires_at = expiration_time
                    self._update_freq_lists(key, node)
                    return

            #add to LFU cache, evict if needed
            new_node: DLLNode[K, V] = DLLNode(key=key, val=value, expires_at=expiration_time)
            self.cache[key] = new_node
            self.node_freq[key] = 1
            self.freq_lists[1].add_to_front(new_node)
            self.min_freq = 1

            if len(self.cache) > self.capacity:
                self._evict_one(now)

                
    def delete(self, key: K) -> bool:
        """
        Return True if key existed and was removed, False otherwise.
        """
        with self._lock:
            node = self.cache.get(key)
            if node is None:
                return False

            self._delete_node(key)
            return True  

    def clear(self) -> None:
        """
        Remove all entries from the cache.
        """
        with self._lock:
            self.cache.clear()
            self.node_freq.clear()
            self.freq_lists.clear()
            self.min_freq = 1

            if self._track_stats:
                self._stats = CacheStats()
  
    def __len__(self) -> int:
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
    
    def contains(self, key: K) -> bool:
        with self._lock:
            node = self.cache.get(key)
            if node is None:
                return False
            if self._is_expired(node):
                self._delete_node(key)
                return False
            return True

    def peek(self, key: K) -> Optional[V]:
        """
        Return value without updating frequency.
        """
        with self._lock:
            node = self.cache.get(key)
            if node is None:
                return None
            if self._is_expired(node):
                self._delete_node(key)
                return None
            return node.val
