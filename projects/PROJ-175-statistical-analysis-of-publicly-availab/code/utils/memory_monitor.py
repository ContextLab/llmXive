"""
Memory Monitoring Utility.

Enforces 6 GB RAM limit for data processing.
"""
import os
import sys
import psutil
import functools
from typing import Callable, Any

MAX_MEMORY_GB = 6

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def track_memory(func: Callable) -> Callable:
    """Decorator to track memory usage before and after function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        mem_before = get_memory_usage_gb()
        print(f"Memory before {func.__name__}: {mem_before:.2f} GB")
        
        result = func(*args, **kwargs)
        
        mem_after = get_memory_usage_gb()
        print(f"Memory after {func.__name__}: {mem_after:.2f} GB")
        print(f"Delta: {mem_after - mem_before:.2f} GB")
        
        if mem_after > MAX_MEMORY_GB:
            print(f"WARNING: Memory usage exceeded {MAX_MEMORY_GB} GB limit!")
        
        return result
    return wrapper

def check_memory_limit():
    """Check if current memory usage is within limits."""
    current = get_memory_usage_gb()
    if current > MAX_MEMORY_GB:
        raise MemoryError(f"Current memory usage {current:.2f} GB exceeds limit of {MAX_MEMORY_GB} GB")
    return True