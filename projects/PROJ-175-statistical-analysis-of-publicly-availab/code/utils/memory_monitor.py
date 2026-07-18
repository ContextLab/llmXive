import os
import sys
import psutil
import functools
from typing import Callable, Any

def get_memory_usage_gb():
    """
    Returns the current memory usage of the process in GB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def track_memory(func: Callable) -> Callable:
    """
    Decorator to track peak memory usage during function execution.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_mem = get_memory_usage_gb()
        result = func(*args, **kwargs)
        end_mem = get_memory_usage_gb()
        # Log or return memory delta if needed, currently just executes
        return result
    return wrapper

def check_memory_limit(limit_mb: int = 6144):
    """
    Checks if current memory usage exceeds the limit.
    Raises MemoryError if limit is exceeded.
    """
    current_gb = get_memory_usage_gb()
    current_mb = current_gb * 1024
    if current_mb > limit_mb:
        raise MemoryError(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb} MB")
    return True
