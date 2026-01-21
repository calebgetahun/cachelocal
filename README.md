# localcache

A thread-safe in-process cache for Python with LRU eviction and optional TTL support.

## Features

- In-memory LRU eviction
- Optional per-entry TTL (lazy expiration)
- Thread-safe via a single lock
- O(1) get/set/delete operations

## Installation

```bash
pip install localcache
```

## Quickstart

```python
from localcache import LRUCache

cache = LRUCache(capacity=2)

cache.set("a", 1)
cache.set("b", 2)

cache.get("a")          # -> 1 (refreshes recency)
cache.set("c", 3)       # evicts "b"

cache.get("b")          # -> None
```

## TTL

```python
cache.set("x", 42, ttl_seconds=1.0)
```

Expired entries are removed on access and may also be removed during eviction when capacity is exceeded.

## Semantics

- Eviction policy: Least Recently Used (LRU)
- TTL: Optional, checked on access (lazy eviction)
- Thread safety: A single lock guards the hashmap and linked list
- Missing/expired keys: `get` returns `None`

## Complexity

- `get`: O(1)
- `set`: O(1)
- `delete`: O(1)

## Development

```bash
pip install -e ".[dev]"
```

## Roadmap

- Additional eviction policies (FIFO, LFU, etc.)
- Optional sharding for reduced lock contention
