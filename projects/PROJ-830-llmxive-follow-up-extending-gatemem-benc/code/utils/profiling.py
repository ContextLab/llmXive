import os
import time
import tracemalloc
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass

from logging_config import setup_logging

logger = setup_logging(__name__)

@dataclass
class ProfileResult:
    start_time: float
    end_time: float
    wall_clock_ms: float
    peak_memory_mb: float

_start_time: Optional[float] = None
_peak_memory: float = 0.0

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    import psutil
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def get_peak_memory_mb() -> float:
    """Get peak memory usage since start profiling or reset."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        return peak / 1024 / 1024
    return _peak_memory

def start_profiling():
    """Start memory and time profiling."""
    global _start_time, _peak_memory
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    _start_time = time.time()
    _peak_memory = 0.0
    logger.info("Profiling started.")

def stop_profiling() -> ProfileResult:
    """Stop profiling and return results."""
    global _start_time
    end_time = time.time()
    if _start_time is None:
        logger.warning("Profiling was not started.")
        return ProfileResult(0, 0, 0, 0)
    
    wall_clock_ms = (end_time - _start_time) * 1000
    peak_mem = get_peak_memory_mb()
    
    tracemalloc.stop()
    _start_time = None
    
    logger.info(f"Profiling stopped. Wall-clock: {wall_clock_ms:.2f}ms, Peak RAM: {peak_mem:.2f}MB")
    return ProfileResult(_start_time, end_time, wall_clock_ms, peak_mem)

def reset_profiling():
    """Reset profiling state."""
    global _start_time, _peak_memory
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    _start_time = None
    _peak_memory = 0.0
    tracemalloc.start()

@contextmanager
def profile_block(label: str = "block"):
    """Context manager to profile a specific block of code."""
    start = time.time()
    start_mem = get_process_memory_mb()
    try:
        yield
    finally:
        end = time.time()
        end_mem = get_process_memory_mb()
        duration_ms = (end - start) * 1000
        logger.debug(f"Block '{label}' took {duration_ms:.2f}ms. Memory delta: {end_mem - start_mem:.2f}MB")

F = TypeVar('F', bound=Callable[..., Any])

def profile_function(label: Optional[str] = None):
    """Decorator to profile a function."""
    def decorator(func: F) -> F:
        def wrapper(*args, **kwargs):
            start = time.time()
            tracemalloc.start()
            try:
                return func(*args, **kwargs)
            finally:
                end = time.time()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                duration_ms = (end - start) * 1000
                func_name = label or func.__name__
                logger.info(f"Function '{func_name}' took {duration_ms:.2f}ms, Peak RAM: {peak/1024/1024:.2f}MB")
        return wrapper # type: ignore
    return decorator

def measure_execution(func: Callable[..., Any]) -> Callable[..., Tuple[Any, ProfileResult]]:
    """Decorator that returns both result and profile result."""
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        start_profiling()
        result = func(*args, **kwargs)
        profile_res = stop_profiling()
        return result, profile_res
    return wrapper

if __name__ == "__main__":
    import time
    
    def test_func():
        time.sleep(0.5)
        return "done"
    
    start_profiling()
    res = test_func()
    profile = stop_profiling()
    print(f"Result: {res}, Time: {profile.wall_clock_ms:.2f}ms, RAM: {profile.peak_memory_mb:.2f}MB")
