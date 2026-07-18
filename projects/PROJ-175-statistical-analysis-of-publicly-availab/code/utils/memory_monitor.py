import os
import sys
import psutil
import functools
from typing import Callable, Any
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def get_memory_usage_gb():
    """Get current memory usage of the process in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def check_memory_limit(limit_mb=6144):
    """Check if current memory usage exceeds the limit."""
    current_gb = get_memory_usage_gb()
    current_mb = current_gb * 1024
    if current_mb > limit_mb:
        raise MemoryError(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb} MB")
    return True

def track_memory(func):
    """Decorator to track memory usage of a function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_mem = get_memory_usage_gb()
        result = func(*args, **kwargs)
        end_mem = get_memory_usage_gb()
        print(f"Function {func.__name__} used {end_mem - start_mem:.4f} GB")
        return result
    return wrapper
