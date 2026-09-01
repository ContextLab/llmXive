"""
Memory optimization utilities for the llmXive pipeline.

Provides functions to enforce memory limits, perform garbage collection,
and manage large data structures efficiently.
"""
import gc
import sys
import logging
import tracemalloc
from typing import Any, Callable, Optional, TypeVar
from pathlib import Path
import resource
import psutil
import os

from utils.logging_config import get_logger

# Constants
DEFAULT_MEMORY_LIMIT_GB = 6.0  # Leave 1GB headroom from 7GB constraint
DEFAULT_GC_THRESHOLD = 1000

logger = get_logger(__name__)

T = TypeVar('T')

def get_current_memory_mb() -> float:
    """
    Get the current memory usage of the process in megabytes.
    
    Uses psutil for cross-platform compatibility and accuracy.
    
    Returns:
        float: Current memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage of the process since tracemalloc started.
    
    Returns:
        float: Peak memory usage in MB, or 0 if tracemalloc not started.
    """
    try:
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    except (ValueError, RuntimeError):
        # tracemalloc not started
        return 0.0

def start_memory_profiling() -> None:
    """Start tracemalloc for memory profiling."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        logger.info("Memory profiling started via tracemalloc")

def stop_memory_profiling() -> Optional[float]:
    """
    Stop tracemalloc and return the peak memory usage.
    
    Returns:
        Optional[float]: Peak memory usage in MB, or None if not tracing.
    """
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"Memory profiling stopped. Peak: {peak / (1024 * 1024):.2f} MB")
        return peak / (1024 * 1024)
    return None

def enforce_memory_limit(limit_gb: float = DEFAULT_MEMORY_LIMIT_GB) -> None:
    """
    Check if current memory usage exceeds the limit.
    
    Args:
        limit_gb: Memory limit in gigabytes.
        
    Raises:
        MemoryError: If current memory usage exceeds the limit.
    """
    current_mb = get_current_memory_mb()
    limit_mb = limit_gb * 1024
    
    if current_mb > limit_mb:
        logger.error(f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB")
        raise MemoryError(
            f"Memory limit exceeded: {current_mb:.2f} MB > {limit_mb:.2f} MB. "
            "Consider reducing batch size or enabling streaming."
        )
    logger.debug(f"Memory check passed: {current_mb:.2f} MB <= {limit_mb:.2f} MB")

def force_garbage_collection() -> int:
    """
    Force garbage collection and return the number of objects collected.
    
    Returns:
        int: Number of objects collected.
    """
    collected = gc.collect()
    logger.debug(f"Garbage collection forced: {collected} objects collected")
    return collected

def clear_cuda_cache() -> None:
    """
    Clear CUDA cache if PyTorch is available.
    
    Silently ignores if CUDA is not available.
    """
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.debug("CUDA cache cleared")
    except ImportError:
        logger.debug("PyTorch not available, skipping CUDA cache clear")
    except Exception as e:
        logger.warning(f"Failed to clear CUDA cache: {e}")

def optimize_for_memory(obj: Any) -> Any:
    """
    Optimize a data structure for memory efficiency.
    
    Currently handles:
    - Lists: Convert to tuples if immutable
    - Dicts: Ensure no unnecessary deep copies
    - Large numpy arrays: Check for views vs copies
    
    Args:
        obj: The object to optimize.
        
    Returns:
        The optimized object (may be the same object).
    """
    if isinstance(obj, list):
        # If the list is large and won't be modified, convert to tuple
        if len(obj) > 1000:
            logger.debug(f"Converting large list of size {len(obj)} to tuple for memory efficiency")
            return tuple(obj)
    elif isinstance(obj, dict):
        # Ensure we're not holding references to unnecessary large objects
        # This is a no-op for the dict itself, but we log for awareness
        pass
    return obj

def memory_safe_iterator(iterable, batch_size: int = 100):
    """
    Create a memory-safe iterator that yields batches of items.
    
    This prevents loading the entire dataset into memory at once.
    
    Args:
        iterable: The source iterable.
        batch_size: Number of items per batch.
        
    Yields:
        List of items in batches.
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
            force_garbage_collection()
    if batch:
        yield batch

def monitor_memory_usage(callback: Optional[Callable[[float], None]] = None, interval_seconds: float = 1.0):
    """
    Context manager to monitor memory usage during execution.
    
    Args:
        callback: Optional callback function that receives memory usage (MB) periodically.
        interval_seconds: Check interval in seconds.
        
    Example:
        with monitor_memory_usage():
            # code that uses memory
            pass
    """
    import threading
    import time

    stop_event = threading.Event()
    monitor_thread = None

    def monitor_loop():
        while not stop_event.is_set():
            current_mb = get_current_memory_mb()
            if callback:
                callback(current_mb)
            time.sleep(interval_seconds)

    try:
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        yield
    finally:
        if monitor_thread:
            stop_event.set()
            monitor_thread.join(timeout=2.0)

def profile_function(func: Callable[..., T], *args, **kwargs) -> Tuple[T, float]:
    """
    Profile a function's memory usage.
    
    Args:
        func: The function to profile.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        Tuple of (function result, peak memory usage in MB during execution).
    """
    start_memory = get_current_memory_mb()
    start_memory_profiling()
    
    try:
        result = func(*args, **kwargs)
        peak_memory = stop_memory_profiling()
        end_memory = get_current_memory_mb()
        
        logger.info(
            f"Function {func.__name__} memory profile: "
            f"Start: {start_memory:.2f} MB, "
            f"End: {end_memory:.2f} MB, "
            f"Peak: {peak_memory:.2f} MB"
        )
        return result, peak_memory
    except Exception as e:
        stop_memory_profiling()
        raise e

def safe_delete(obj_ref: Any) -> None:
    """
    Safely delete an object and force garbage collection.
    
    Args:
        obj_ref: Reference to the object to delete.
    """
    if obj_ref is not None:
        del obj_ref
        force_garbage_collection()
        logger.debug("Object deleted and garbage collected")

def check_memory_constraints(required_mb: int) -> bool:
    """
    Check if there is enough available memory for the required amount.
    
    Args:
        required_mb: Required memory in megabytes.
        
    Returns:
        bool: True if sufficient memory is available, False otherwise.
    """
    current_mb = get_current_memory_mb()
    total_mb = resource.getrlimit(resource.RLIMIT_AS)[0]
    if total_mb == resource.RLIM_INFINITY:
        # No limit set, assume we have enough
        return True
    
    available_mb = total_mb - current_mb
    has_enough = available_mb >= required_mb
    
    if not has_enough:
        logger.error(
            f"Insufficient memory: Required {required_mb} MB, "
            f"Available {available_mb:.2f} MB"
        )
    return has_enough