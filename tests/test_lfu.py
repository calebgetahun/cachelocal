import time
import pytest
from cachelocal import LFUCache

@pytest.fixture
def cache():
    return LFUCache(capacity=2, track_stats=True)

def test_get_missing(cache):
    assert cache.get("x") is None

def test_set_get(cache):
    cache.set("a", 1)
    assert cache.get("a") == 1

def test_eviction_lfu(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")     # a has freq=2, b has freq=1
    cache.set("c", 3)  # evict b (lowest freq)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3

def test_eviction_lru_tiebreak(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # both a,b at freq=1; a is LRU so evicted
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3

def test_update_does_not_evict_self(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("a", 10)  # update bumps a's freq
    cache.set("c", 3)   # should evict b (freq=1), not a (freq=2)
    assert cache.get("b") is None
    assert cache.get("a") == 10
    assert cache.get("c") == 3

def test_delete(cache):
    cache.set("a", 1)
    assert cache.delete("a") is True
    assert cache.get("a") is None
    assert cache.delete("a") is False

def test_ttl_expires_lazy(cache):
    cache.set("a", 1, ttl_seconds=0.01)
    cache.set("b", 2)
    time.sleep(0.02)
    assert cache.get("a") is None
    assert cache.get("b") == 2

def test_contains_no_freq_bump(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.contains("a")  # should NOT bump freq
    cache.set("c", 3)    # a and b both freq=1, a is LRU
    assert cache.get("a") is None  # a evicted, not b

def test_peek_no_freq_bump(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.peek("a") == 1  # should NOT bump freq
    cache.set("c", 3)
    assert cache.get("a") is None  # a evicted

def test_clear(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None

def test_expired_key_set_resets_freq(cache):
    cache.set("a", 1, ttl_seconds=0.01)
    cache.get("a")  # freq=2
    cache.get("a")  # freq=3
    time.sleep(0.02)
    cache.set("a", 10)  # expired, should reset to freq=1
    cache.set("b", 2)
    cache.set("c", 3)   # should evict a (freq=1), not b
    assert cache.get("a") is None
    assert cache.get("b") == 2

def test_capacity_one():
    cache = LFUCache(capacity=1, track_stats=True)
    cache.set("a", 1)
    cache.set("b", 2)  # evicts a
    assert cache.get("a") is None
    assert cache.get("b") == 2

def test_stats_disabled():
    cache = LFUCache(capacity=2, track_stats=False)
    cache.set("a", 1)
    cache.get("a")
    stats = cache.get_stats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.evictions == 0

def test_stats_hits_and_misses(cache):
    cache.set("a", 1)
    cache.get("a")  # hit
    cache.get("b")  # miss
    stats = cache.get_stats()
    assert stats.hits == 1
    assert stats.misses == 1

def test_stats_evictions(cache):
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # triggers eviction
    stats = cache.get_stats()
    assert stats.evictions == 1

