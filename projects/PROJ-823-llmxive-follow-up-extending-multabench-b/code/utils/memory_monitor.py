import psutil
import os
from typing import Optional

def get_process_memory_mb() -> float:
    """Returns the current memory usage of the process in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def memory_limit_context(limit_mb: float = 6500):
    """
    Context manager to check memory usage.
    Raises MemoryError if limit exceeded.
    """
    import functools
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if get_process_memory_mb() > limit_mb:
                raise MemoryError(f"Memory limit ({limit_mb}MB) exceeded. Current: {get_process_memory_mb():.2f}MB")
            return func(*args, **kwargs)
        return wrapper
    return decorator
