from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Generic, Hashable, TypeVar, Optional

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

class Cache(ABC, Generic[K, V]):
    """
    Abstract cache interface.

    Implementations (LRU, LFU, FIFO, etc.) should be drop-in replaceable.
    """

    @abstractmethod
    def get(self, key: K) -> Optional[V]:
        """
        Return value associated with key if exists within cache and not expired, None otherwise.
        """
        ...

    @abstractmethod
    def set(self, key: K, value: V, ttl_seconds: Optional[float] = None) -> None:
        """
        ttl is in seconds. If ttl is None, entry has no expiration.
        """
        ...

    @abstractmethod
    def delete(self, key: K) -> bool:
        """
        Return True if key existed and was removed, False otherwise.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all entries from the cache.
        """
        ...

    @abstractmethod
    def __len__(self) -> int:
        """
        Returns number of entries in cache
        """
        ...
