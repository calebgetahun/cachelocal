"""
Simple benchmarks for cache implementations.

"""
import time
from functools import lru_cache
from cachelocal import LRUCache, FIFOCache

def benchmark_cache(cache_factory, name: str, operations: int = 100_000):
    """Benchmark a cache implementation."""
    cache = cache_factory()
    
    # Warm up
    for i in range(100):
        cache.set(f"key_{i}", i)
        cache.get(f"key_{i}")
    
    # Benchmark writes
    start = time.perf_counter()
    for i in range(operations):
        cache.set(f"key_{i % 1000}", i)
    write_time = time.perf_counter() - start
    
    # Benchmark reads (mix of hits and misses)
    start = time.perf_counter()
    for i in range(operations):
        cache.get(f"key_{i % 1500}")  # 1000 hits, 500 misses
    read_time = time.perf_counter() - start
    
    # Benchmark mixed workload
    start = time.perf_counter()
    for i in range(operations):
        if i % 3 == 0:
            cache.set(f"key_{i % 1000}", i)
        else:
            cache.get(f"key_{i % 1500}")
    mixed_time = time.perf_counter() - start
    
    print(f"\n{name}:")
    print(f"  Writes:  {operations:,} ops in {write_time:.3f}s ({operations/write_time:,.0f} ops/sec)")
    print(f"  Reads:   {operations:,} ops in {read_time:.3f}s ({operations/read_time:,.0f} ops/sec)")
    print(f"  Mixed:   {operations:,} ops in {mixed_time:.3f}s ({operations/mixed_time:,.0f} ops/sec)")


def benchmark_cache_readonly(cache_factory, name: str, operations: int = 100_000):
    """Benchmark read-only workload (fair comparison with functools.lru_cache)."""
    cache = cache_factory()
    
    # Pre-populate cache
    for i in range(1000):
        cache.set(f"key_{i}", i)
    
    # Benchmark pure reads (mix of hits and misses)
    start = time.perf_counter()
    for i in range(operations):
        cache.get(f"key_{i % 1500}")  # 1000 hits, 500 misses
    read_time = time.perf_counter() - start
    
    print(f"{name}:")
    print(f"  Read-only: {operations:,} ops in {read_time:.3f}s ({operations/read_time:,.0f} ops/sec)")


def benchmark_functools_lru(operations: int = 100_000):
    """Benchmark functools.lru_cache for comparison."""
    
    @lru_cache(maxsize=1000)
    def cached_func(key):
        return key * 2
    
    # Warm up
    for i in range(100):
        cached_func(i)
    
    # Benchmark (only reads, since lru_cache doesn't have explicit set)
    start = time.perf_counter()
    for i in range(operations):
        cached_func(i % 1500)
    read_time = time.perf_counter() - start
    
    print(f"functools.lru_cache:")
    print(f"  Read-only: {operations:,} ops in {read_time:.3f}s ({operations/read_time:,.0f} ops/sec)")


if __name__ == "__main__":
    print("=" * 60)
    print("Cache Benchmarks")
    print("=" * 60)
    
    operations = 100_000
    
    # Full workload benchmarks
    print("\nFull Workload (Writes, Reads, Mixed):")
    print("-" * 60)
    
    # LRU with stats
    benchmark_cache(
        lambda: LRUCache(capacity=1000, track_stats=True),
        "LRUCache (stats=True)",
        operations
    )
    
    # LRU without stats
    benchmark_cache(
        lambda: LRUCache(capacity=1000, track_stats=False),
        "LRUCache (stats=False)",
        operations
    )
    
    # FIFO with stats
    benchmark_cache(
        lambda: FIFOCache(capacity=1000, track_stats=True),
        "FIFOCache (stats=True)",
        operations
    )
    
    # FIFO without stats
    benchmark_cache(
        lambda: FIFOCache(capacity=1000, track_stats=False),
        "FIFOCache (stats=False)",
        operations
    )
    
    # Read-only comparison
    print("\n" + "=" * 60)
    print("Read-Only Comparison (vs functools.lru_cache)")
    print("=" * 60)
    print()
    
    benchmark_cache_readonly(
        lambda: LRUCache(capacity=1000, track_stats=False),
        "LRUCache (stats=False)",
        operations
    )
    
    benchmark_cache_readonly(
        lambda: FIFOCache(capacity=1000, track_stats=False),
        "FIFOCache (stats=False)",
        operations
    )
    
    benchmark_functools_lru(operations)
    
    print("\n" + "=" * 60)