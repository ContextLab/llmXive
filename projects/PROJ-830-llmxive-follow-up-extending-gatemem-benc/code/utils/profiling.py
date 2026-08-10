import os
import time
import tracemalloc
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, field
import psutil

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from code.logging_config import setup_logging

logger = setup_logging(__name__)

@dataclass
class ProfileResult:
    """Container for profiling results."""
    start_time: float
    end_time: float
    duration_ms: float
    peak_memory_mb: float
    current_memory_mb: float
    task_id: Optional[str] = None
    domain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "peak_memory_mb": self.peak_memory_mb,
            "current_memory_mb": self.current_memory_mb,
            "task_id": self.task_id,
            "domain": self.domain
        }

# Global state for profiling
_tracemalloc_active = False
_start_time = 0.0
_start_memory = 0.0
_peak_memory = 0.0

def get_process_memory_mb() -> float:
    """
    Get the current resident set size (RSS) memory usage of the process in MB.
    Uses psutil for accurate cross-platform memory measurement.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage recorded by tracemalloc in MB.
    Returns 0.0 if tracemalloc is not active.
    """
    if not _tracemalloc_active:
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def start_profiling() -> None:
    """
    Start global memory and time profiling.
    Initializes tracemalloc and records start time.
    """
    global _tracemalloc_active, _start_time, _start_memory, _peak_memory
    
    if not _tracemalloc_active:
        tracemalloc.start()
        _tracemalloc_active = True
        logger.debug("tracemalloc started for profiling")
    
    _start_time = time.perf_counter()
    _start_memory = get_process_memory_mb()
    _peak_memory = _start_memory
    logger.debug(f"Profiling started. Initial memory: {_start_memory:.2f} MB")

def stop_profiling() -> ProfileResult:
    """
    Stop profiling and return the result.
    
    Returns:
        ProfileResult: Object containing duration and memory metrics.
    """
    global _tracemalloc_active, _start_time, _peak_memory
    
    end_time = time.perf_counter()
    duration_ms = (end_time - _start_time) * 1000
    
    current_mem = get_process_memory_mb()
    peak_mem = get_peak_memory_mb()
    
    # Update global peak if current is higher
    if current_mem > _peak_memory:
        _peak_memory = current_mem
    
    result = ProfileResult(
        start_time=_start_time,
        end_time=end_time,
        duration_ms=duration_ms,
        peak_memory_mb=peak_mem if peak_mem > 0 else _peak_memory,
        current_memory_mb=current_mem
    )
    
    logger.debug(f"Profiling stopped. Duration: {duration_ms:.2f}ms, Peak RAM: {result.peak_memory_mb:.2f} MB")
    return result

def reset_profiling() -> None:
    """
    Reset global profiling state without stopping tracemalloc.
    Useful for measuring multiple segments independently.
    """
    global _start_time, _start_memory, _peak_memory
    _start_time = time.perf_counter()
    _start_memory = get_process_memory_mb()
    _peak_memory = _start_memory
    logger.debug("Profiling state reset")

@contextmanager
def profile_block(task_id: Optional[str] = None, domain: Optional[str] = None) -> Any:
    """
    Context manager to profile a specific block of code.
    
    Args:
        task_id: Optional identifier for the task being profiled.
        domain: Optional domain name for categorization.
        
    Yields:
        ProfileResult: The result of the profiling operation.
    """
    start_time = time.perf_counter()
    start_mem = get_process_memory_mb()
    
    # Ensure tracemalloc is running if not already
    if not _tracemalloc_active:
        tracemalloc.start()
        _tracemalloc_active = True
    
    try:
        yield ctx
    finally:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        current_mem = get_process_memory_mb()
        peak_mem = get_peak_memory_mb()
        
        result = ProfileResult(
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            peak_memory_mb=peak_mem,
            current_memory_mb=current_mem,
            task_id=task_id,
            domain=domain
        )
        
        logger.info(f"Block '{task_id}' profiled: {duration_ms:.2f}ms, Peak: {peak_mem:.2f} MB")
        return result

@contextmanager
def profile_function(func: Callable) -> Callable:
    """
    Decorator-style context manager to profile a function call.
    
    Args:
        func: The function to profile.
        
    Returns:
        Wrapped function that returns (result, ProfileResult).
    """
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        start_mem = get_process_memory_mb()
        
        if not _tracemalloc_active:
            tracemalloc.start()
            _tracemalloc_active = True
        
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            current_mem = get_process_memory_mb()
            peak_mem = get_peak_memory_mb()
            
            logger.info(f"Function '{func.__name__}' executed: {duration_ms:.2f}ms, Peak: {peak_mem:.2f} MB")
            # Note: In a real implementation, we might want to attach the profile result to the return value
            # For now, we just log it. The caller can access global stats if needed.
        
        return result
    
    return wrapper

def measure_execution(func: Callable, *args, **kwargs) -> tuple:
    """
    Execute a function and measure its execution time and memory usage.
    
    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        tuple: (function_return_value, ProfileResult)
    """
    start_time = time.perf_counter()
    start_mem = get_process_memory_mb()
    
    if not _tracemalloc_active:
        tracemalloc.start()
        _tracemalloc_active = True
    
    try:
        result = func(*args, **kwargs)
    finally:
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        current_mem = get_process_memory_mb()
        peak_mem = get_peak_memory_mb()
        
        profile_result = ProfileResult(
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            peak_memory_mb=peak_mem,
            current_memory_mb=current_mem
        )
        
        logger.debug(f"Function '{func.__name__}' measured: {duration_ms:.2f}ms, Peak: {peak_mem:.2f} MB")
    
    return result, profile_result

def main():
    """
    Main entry point for testing the profiling module.
    Runs a simple benchmark to demonstrate functionality.
    """
    logger.info("Starting profiling module self-test")
    
    # Start global profiling
    start_profiling()
    
    # Simulate some work
    data = []
    for i in range(100000):
        data.append(i * i)
    
    # Stop profiling
    result = stop_profiling()
    
    print(f"Self-test Results:")
    print(f"  Duration: {result.duration_ms:.2f} ms")
    print(f"  Peak Memory: {result.peak_memory_mb:.2f} MB")
    print(f"  Current Memory: {result.current_memory_mb:.2f} MB")
    
    # Test context manager
    with profile_block(task_id="test_block", domain="self_test") as block_result:
        _ = sum(range(10000))
    
    print(f"  Block Duration: {block_result.duration_ms:.2f} ms")
    print(f"  Block Peak Memory: {block_result.peak_memory_mb:.2f} MB")

if __name__ == "__main__":
    # Setup basic logging if running standalone
    logging.basicConfig(level=logging.INFO)
    main()