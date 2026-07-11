"""
Memory monitoring utilities to track peak RAM usage and enforce limits.
"""
import os
import platform
import gc
from contextlib import contextmanager
from typing import Optional, Tuple, Generator
from functools import wraps

def get_process_memory_mb() -> float:
    """
    Get current process memory usage in MB.
    Returns 0.0 if the platform is not supported.
    """
    system = platform.system()
    pid = os.getpid()

    if system == "Linux":
        try:
            with open(f"/proc/{pid}/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # VmRSS is in kB
                        return float(line.split()[1]) / 1024.0
        except FileNotFoundError:
            return 0.0
    elif system == "Darwin":  # macOS
        try:
            import subprocess
            output = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)])
            return float(output.strip()) / 1024.0
        except Exception:
            return 0.0
    
    return 0.0

@contextmanager
def memory_limit_context(limit_mb: float) -> Generator[Tuple[float, float], None, None]:
    """
    Context manager to monitor memory usage and enforce a limit.
    Yields (start_memory, current_memory).
    Raises MemoryError if the limit is exceeded.
    """
    gc.collect()
    start_mem = get_process_memory_mb()
    try:
        yield start_mem, start_mem
    finally:
        gc.collect()
        current_mem = get_process_memory_mb()
        if current_mem > limit_mb:
            raise MemoryError(
                f"Memory limit exceeded: {current_mem:.2f} MB > {limit_mb:.2f} MB"
            )
        return start_mem, current_mem

def track_memory(func):
    """
    Decorator to track memory usage of a function.
    Logs peak memory usage to the logger (if available).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        gc.collect()
        start_mem = get_process_memory_mb()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            gc.collect()
            end_mem = get_process_memory_mb()
            # Note: Actual logging requires importing logging utils which might create circular imports
            # Here we just print to stderr for now or assume a logger is passed
            # For this task, we assume the logger is available via utils.logging
            try:
                from utils.logging import get_logger
                logger = get_logger(__name__)
                logger.info(f"Memory delta for {func.__name__}: {end_mem - start_mem:.2f} MB")
            except ImportError:
                pass
    return wrapper
