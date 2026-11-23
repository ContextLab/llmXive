"""
Memory and time monitoring utilities for generation tasks.
"""
import os
import sys
import time
import signal
from pathlib import Path
from typing import Optional, Callable, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds limit."""
    pass

class TimeLimitExceededError(Exception):
    """Raised when execution time exceeds limit."""
    pass

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback if psutil not available
        return 0.0

def check_memory_limit(limit_mb: float = 8000) -> bool:
    """Check if current memory usage is within limit."""
    usage = get_memory_usage_mb()
    return usage < limit_mb

def enforce_memory_limit(limit_mb: float = 8000):
    """Enforce memory limit, raise error if exceeded."""
    if not check_memory_limit(limit_mb):
        raise MemoryLimitExceededError(f"Memory limit exceeded: {get_memory_usage_mb():.2f}MB > {limit_mb}MB")

class TimeLimitEnforcer:
    """Context manager for enforcing time limits."""
    
    def __init__(self, timeout_seconds: int):
        self.timeout = timeout_seconds
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout:
            raise TimeLimitExceededError(f"Time limit exceeded: {elapsed:.2f}s > {self.timeout}s")
        return False

def monitor_batch_generation(func: Callable, timeout_seconds: int = 3600):
    """Decorator to monitor batch generation with time limits."""
    def wrapper(*args, **kwargs):
        with TimeLimitEnforcer(timeout_seconds):
            return func(*args, **kwargs)
    return wrapper

def main():
    """Entry point for memory monitor (utility)."""
    pass

if __name__ == '__main__':
    main()
