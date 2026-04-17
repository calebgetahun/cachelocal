from .base import Cache
from .lru import LRUCache
from .fifo import FIFOCache
from .lfu import LFUCache

__all__ = ["Cache", "LRUCache", "FIFOCache", "LFUCache"]
