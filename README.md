# cachelocal

A thread-safe in-process cache for Python with multiple eviction policies and optional TTL support.

## Features

- Multiple eviciton policies: LRU, FIFO
- Optional per-entry TTL (lazy expiration)
- Thread-safe via a single lock
- O(1) get/set/delete operations
- Optional stats tracking (hits, misses, evictions)

## Installation

```bash
pip install cachelocal
```

## Quickstart

### LRU Cache

```python
from cachelocal import LRUCache

cache = LRUCache(capacity=2)

cache.set("a", 1)
cache.set("b", 2)

cache.get("a")          # -> 1 (refreshes recency)
cache.set("c", 3)       # evicts "b"

cache.get("b")          # -> None
```

### FIFO Cache

```python
from cachelocal import FIFOCache

cache = FIFOCache(capacity=2)

cache.set("a", 1)
cache.set("b", 2)

cache.get("a")          # -> 1 (does NOT refresh position)
cache.set("c", 3)       # evicts "a" (oldest insertion)

cache.get("a")          # -> None
```

## TTL

```python
cache.set("x", 42, ttl_seconds=1.0)
```

Expired entries are removed on access and may also be removed during eviction when capacity is exceeded.

## Stats Tracking

```python
cache = LRUCache(capacity=100, track_stats=True)

cache.set("a", 1)
cache.get("a")  # hit
cache.get("b")  # miss

stats = cache.get_stats()
print(f"Hits: {stats.hits}, Misses: {stats.misses}, Evictions: {stats.evictions}")
```

## Performance

Benchmarks on Apple M-series (100k operations):

### Read-Only Workload

| Implementation      | ops/sec | vs functools |
| ------------------- | ------- | ------------ |
| FIFOCache           | 3.7M    | 35%          |
| LRUCache            | 2.5M    | 24%          |
| functools.lru_cache | 10.6M   | baseline     |

### Mixed Workload (stats disabled)

| Implementation | Writes     | Reads      | Mixed      |
| -------------- | ---------- | ---------- | ---------- |
| FIFOCache      | 3.7M ops/s | 3.7M ops/s | 3.3M ops/s |
| LRUCache       | 2.3M ops/s | 2.7M ops/s | 2.4M ops/s |

**Key takeaways:**

- FIFO is ~48% faster than LRU (no recency updates on access)
- Stats tracking overhead: ~5-10%
- Both implementations handle millions of operations per second

Run benchmarks yourself:

```bash
python benchmarks/benchmark.py
```

## Semantics

### LRU Cache

- Eviction policy: Least Recently Used
- Access behavior: `get()` and `set()` refresh recency
- Best for: General-purpose caching with access-based eviction

### FIFO Cache

- Eviction policy: First In, First Out
- Access behavior: `get()` does NOT refresh position
- Best for: Time-windowed data, session caches

### Both

- TTL: Optional, checked on access (lazy eviction)
- Thread safety: Single lock guards hashmap and linked list
- Missing/expired keys: `get()` returns `None`

## Complexity

- `get()`: O(1)
- `set()`: O(1)
- `delete()`: O(1)

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Roadmap

- Additional eviction policies (LFU, ARC)
- Optional sharding for reduced lock contention
- Async support
