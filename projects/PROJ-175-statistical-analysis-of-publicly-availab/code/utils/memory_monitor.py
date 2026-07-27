import os
import sys
import psutil
import functools
from typing import Callable, Any
import json

def get_memory_usage_gb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024 / 1024

def check_memory_limit(limit_mb=6144):
    current_mb = get_memory_usage_gb() * 1024
    if current_mb > limit_mb:
        raise MemoryError(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb} MB")
    return True

def track_memory(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
