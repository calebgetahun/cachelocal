import time
import pytest
from cachelocal import LRUCache

@pytest.fixture
def cache():
    return LRUCache(capacity=2, track_stats=True)

def test_get_missing(cache):
    assert cache.get("x") is None

def test_set_get(cache):
    cache.set("a", 1)
    assert cache.get("a") == 1

def test_eviction_lru(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    _ = cache.get("a")      # refresh a; b becomes LRU
    cache.set("c", 3)       # evict b
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3

def test_update_refreshes_recency(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("a", 10)      # update should refresh a
    cache.set("c", 3)       # should evict b
    assert cache.get("b") is None
    assert cache.get("a") == 10

def test_ttl_expires_lazy(cache):
    cache.set("a", 1, ttl_seconds=0.01)
    cache.set("b", 2)
    cache.get("a")
    time.sleep(0.02)
    cache.set("c", 3)
    assert len(cache) == 2
    assert cache.get("a") is None

def test_delete(cache):
    cache.set("a", 1)
    assert cache.delete("a") is True
    assert cache.delete("a") is False

def test_set_prefers_evicted_expired(cache):
    cache.set("a", 1, ttl_seconds=0.01)
    cache.set("b", 2)

    assert cache.get("a") == 1
    time.sleep(0.02)

    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3

def test_stats_disabled():
    cache = LRUCache(capacity=2, track_stats=False)
    cache.set("a", 1)
    cache.get("a")
    stats = cache.get_stats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.evictions == 0

def test_stats(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    cache.get("a")
    cache.get("b")
    cache.get("d")

    stats = cache.get_stats()

    assert stats.hits == 1
    assert stats.misses == 2
    assert stats.evictions == 1