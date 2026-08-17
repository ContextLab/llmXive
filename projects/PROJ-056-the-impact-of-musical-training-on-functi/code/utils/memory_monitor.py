"""
Memory monitoring utilities.
Implements T005.
"""
import os
import resource
from typing import Optional

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the limit."""
    pass

def get_current_memory_mb() -> float:
    """Get current RSS memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0

def check_memory_limit(limit_mb: float = 7000) -> None:
    """
    Check if current memory usage exceeds limit.
    Raises MemoryLimitExceeded if limit is exceeded.
    """
    current = get_current_memory_mb()
    if current > limit_mb:
        raise MemoryLimitExceeded(f"Memory limit exceeded: {current:.2f} MB > {limit_mb} MB")

def enforce_memory_limit(limit_mb: float = 7000) -> None:
    """Enforce memory limit, raising exception if exceeded."""
    check_memory_limit(limit_mb)

def get_memory_usage_report() -> dict:
    """Get a report of memory usage."""
    return {
        'current_mb': get_current_memory_mb(),
        'limit_mb': 7000
    }

def simulate_large_memory_usage(size_mb: int) -> None:
    """Simulate large memory usage for testing."""
    data = bytearray(size_mb * 1024 * 1024)
    # Force allocation
    _ = len(data)

def cleanup_large_memory() -> None:
    """Attempt to cleanup large memory allocations."""
    import gc
    gc.collect()
