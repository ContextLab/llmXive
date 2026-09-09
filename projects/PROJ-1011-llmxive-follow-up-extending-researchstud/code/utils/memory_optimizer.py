"""
Memory optimization utilities for the llmXive pipeline.

This module provides tools for monitoring, enforcing, and optimizing
memory usage during data processing and model inference tasks.
"""
import gc
import sys
import logging
import tracemalloc
from typing import Any, Callable, Optional, TypeVar, Iterator, List
from pathlib import Path
import os
import resource
import numpy as np
import torch

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MEMORY_LIMIT_MB = 6000  # Leave headroom below 7GB limit
SAFE_DELETE_THRESHOLD = 100  # MB to trigger aggressive cleanup

T = TypeVar('T')


def get_current_memory_mb() -> float:
    """
    Get current memory usage in MB.
    
    Returns:
        Current memory usage in megabytes.
    """
    if sys.platform == 'darwin':
        # macOS uses resource module
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024  # Convert KB to MB
    else:
        # Linux/Windows
        return tracemalloc.get_traced_memory()[1] / (1024 * 1024)


def get_peak_memory_mb() -> float:
    """
    Get peak memory usage since tracemalloc started.
    
    Returns:
        Peak memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        return 0.0
    return tracemalloc.get_traced_memory()[1] / (1024 * 1024)


def start_memory_profiling() -> None:
    """Start memory profiling with tracemalloc."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        logger.debug("Memory profiling started")


def stop_memory_profiling() -> None:
    """Stop memory profiling and log results."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"Memory profiling stopped: current={current/1024/1024:.2f}MB, peak={peak/1024/1024:.2f}MB")


def enforce_memory_limit(limit_mb: Optional[float] = None) -> None:
    """
    Enforce a hard memory limit. Raises MemoryError if exceeded.
    
    Args:
        limit_mb: Memory limit in MB. Defaults to DEFAULT_MEMORY_LIMIT_MB.
        
    Raises:
        MemoryError: If current memory usage exceeds the limit.
    """
    if limit_mb is None:
        limit_mb = DEFAULT_MEMORY_LIMIT_MB
        
    current = get_current_memory_mb()
    if current > limit_mb:
        logger.error(f"Memory limit exceeded: {current:.2f}MB > {limit_mb:.2f}MB")
        raise MemoryError(f"Memory limit exceeded: {current:.2f}MB > {limit_mb:.2f}MB")
    logger.debug(f"Memory check passed: {current:.2f}MB <= {limit_mb:.2f}MB")


def force_garbage_collection() -> int:
    """
    Force garbage collection and return collected object count.
    
    Returns:
        Number of objects collected.
    """
    collected = gc.collect()
    logger.debug(f"Garbage collection: {collected} objects collected")
    return collected


def clear_cuda_cache() -> None:
    """Clear CUDA cache if GPU is available."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        logger.debug("CUDA cache cleared")


def optimize_for_memory(obj: Any) -> Any:
    """
    Optimize an object for memory efficiency.
    
    Args:
        obj: Object to optimize (numpy arrays, torch tensors, lists, dicts).
        
    Returns:
        Memory-optimized version of the object.
    """
    if isinstance(obj, np.ndarray):
        # Convert to more compact dtype if possible
        if obj.dtype == np.float64:
            obj = obj.astype(np.float32)
        elif obj.dtype == np.int64:
            obj = obj.astype(np.int32)
        # Ensure contiguous memory layout
        obj = np.ascontiguousarray(obj)
        return obj
        
    elif isinstance(obj, torch.Tensor):
        if obj.dtype == torch.float64:
            obj = obj.to(torch.float32)
        elif obj.dtype == torch.int64:
            obj = obj.to(torch.int32)
        if obj.is_cuda:
            obj = obj.cpu()
        return obj
        
    elif isinstance(obj, list):
        # Recursively optimize list items
        return [optimize_for_memory(item) for item in obj]
        
    elif isinstance(obj, dict):
        # Recursively optimize dict values
        return {k: optimize_for_memory(v) for k, v in obj.items()}
        
    return obj


def memory_safe_iterator(iterable: Iterator[T], 
                         chunk_size: int = 100,
                         limit_mb: Optional[float] = None) -> Iterator[T]:
    """
    Iterator that enforces memory limits and triggers cleanup periodically.
    
    Args:
        iterable: Source iterator.
        chunk_size: Number of items to process before memory check.
        limit_mb: Memory limit in MB.
        
    Yields:
        Items from the iterator with periodic memory management.
    """
    count = 0
    for item in iterable:
        yield item
        count += 1
        
        if count % chunk_size == 0:
            # Periodic cleanup
            force_garbage_collection()
            if limit_mb:
                enforce_memory_limit(limit_mb)
            clear_cuda_cache()


def monitor_memory_usage(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to monitor memory usage of a function.
    
    Args:
        func: Function to wrap.
        
    Returns:
        Wrapped function with memory monitoring.
    """
    def wrapper(*args, **kwargs) -> T:
        start_mem = get_current_memory_mb()
        start_profile = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
        
        result = func(*args, **kwargs)
        
        end_mem = get_current_memory_mb()
        end_profile = tracemalloc.get_traced_memory()[1] if tracemalloc.is_tracing() else 0
        
        delta = end_mem - start_mem
        profile_delta = (end_profile - start_profile) / (1024 * 1024)
        
        logger.info(
            f"Function {func.__name__} memory usage: "
            f"delta={delta:.2f}MB, profile_delta={profile_delta:.2f}MB"
        )
        
        return result
        
    return wrapper


def profile_function(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to profile memory usage with detailed snapshot.
    
    Args:
        func: Function to profile.
        
    Returns:
        Wrapped function with detailed memory profiling.
    """
    def wrapper(*args, **kwargs) -> T:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        snapshot_before = tracemalloc.take_snapshot()
        start_mem = get_current_memory_mb()
        
        result = func(*args, **kwargs)
        
        snapshot_after = tracemalloc.take_snapshot()
        end_mem = get_current_memory_mb()
        
        # Calculate top memory consumers
        stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        top_stats = stats[:10]
        
        logger.info(f"Function {func.__name__} memory delta: {end_mem - start_mem:.2f}MB")
        for stat in top_stats:
            logger.debug(f"  {stat}")
        
        return result
        
    return wrapper


def safe_delete(obj: Any) -> None:
    """
    Safely delete an object and force cleanup.
    
    Args:
        obj: Object to delete.
    """
    if obj is not None:
        del obj
        force_garbage_collection()
        clear_cuda_cache()


def check_memory_constraints(required_mb: float, 
                             safety_factor: float = 1.2) -> bool:
    """
    Check if there is enough memory available for the required amount.
    
    Args:
        required_mb: Required memory in MB.
        safety_factor: Safety margin multiplier.
        
    Returns:
        True if sufficient memory is available, False otherwise.
    """
    current = get_current_memory_mb()
    required_with_safety = required_mb * safety_factor
    
    # Estimate available memory (assuming 7GB limit)
    available = 7000 - current
    
    if available < required_with_safety:
        logger.warning(
            f"Insufficient memory: need {required_with_safety:.2f}MB, "
            f"have {available:.2f}MB available (current: {current:.2f}MB)"
        )
        return False
        
    logger.debug(
        f"Memory check passed: need {required_with_safety:.2f}MB, "
        f"have {available:.2f}MB available"
    )
    return True
