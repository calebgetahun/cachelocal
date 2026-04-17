# cachelocal

A thread-safe in-process cache for Python with multiple eviction policies and optional TTL support.

## Motivation

Python's `functools.lru_cache` is fast (~9M ops/sec) but limited: no TTL, no cache introspection (`contains`/`peek` without triggering the wrapped function), no eviction policy options, and no stats. I hit this limitation building a [Rubik's Cube solver](https://github.com/calebgetahun/puzzle-solver) that needed to check cache membership before deciding whether to fall through to Redis or the Kociemba solver. cachelocal provides that introspection alongside multiple eviction policies and per-entry TTL.

## Features

- Multiple eviction policies: LRU, FIFO, LFU
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

### LFU Cache

```python
from cachelocal import LFUCache

cache = LFUCache(capacity=2)

cache.set("a", 1)
cache.set("b", 2)

cache.get("a")          # -> 1 (a: freq=2, b: freq=1)
cache.get("a")          # -> 1 (a: freq=3, b: freq=1)
cache.set("c", 3)       # evicts "b" (lowest frequency)

cache.get("b")          # -> None

cache.contains("a")     # -> True (no freq bump)
cache.peek("a")         # -> 1 (no freq bump)
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
| FIFOCache           | 2.9M    | 32%          |
| LRUCache            | 2.0M    | 23%          |
| LFUCache            | 1.7M    | 20%          |
| functools.lru_cache | 8.9M    | baseline     |

### Mixed Workload (stats disabled)

| Implementation | Writes     | Reads      | Mixed      |
| -------------- | ---------- | ---------- | ---------- |
| FIFOCache      | 3.3M ops/s | 3.4M ops/s | 3.1M ops/s |
| LRUCache       | 2.0M ops/s | 2.4M ops/s | 2.1M ops/s |
| LFUCache       | 1.6M ops/s | 1.9M ops/s | 1.5M ops/s |

**Key takeaways:**

- FIFO is fastest (no reordering on access)
- LRU is ~30% faster than LFU (simpler bookkeeping per operation)
- LFU is slowest but provides frequency-aware eviction
- All implementations handle 1.5M+ operations per second
- functools.lru_cache is ~4-5x faster (C implementation) but lacks TTL, introspection, and policy options

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

### LFU Cache

- Eviction policy: Least Frequently Used
- Access behavior: `get()` increments frequency; ties broken by LRU within the same frequency bucket
- Best for: Workloads where popular entries should be retained regardless of recency

### All Caches

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

- Cache introspection (`contains`/`peek`) for LRU and FIFO
- Additional eviction policies (ARC)
- Optional sharding for reduced lock contention
- Async support
