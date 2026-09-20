"""
Utility functions for batch processing, memory management, and error handling.
"""
import os
import gc
import torch
from typing import Iterable, Iterator, TypeVar
from collections.abc import Sequence
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

def batch_iterator(iterable: Iterable[T], batch_size: int) -> Iterator[List[T]]:
    """
    Yields chunks of size `batch_size` from `iterable`.
    
    Args:
        iterable: The iterable to chunk.
        batch_size: The size of each chunk.
        
    Yields:
        A list of items of size `batch_size` (or smaller for the last chunk).
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.
    Note: This is a simplified approximation for Linux.
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KB
        return usage / (1024 * 1024)
    except Exception:
        # Fallback to torch if resource is unavailable
        if torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / (1024 * 1024 * 1024)
        return 0.0

def memory_guard(threshold_gb: float) -> bool:
    """
    Returns `True` if current RAM usage < `threshold_gb`, else raises a `MemoryError`.
    
    Args:
        threshold_gb: The memory threshold in GB.
        
    Raises:
        MemoryError: If current RAM usage exceeds the threshold.
        
    Returns:
        True if usage is below threshold.
    """
    current_usage = get_memory_usage_gb()
    if current_usage >= threshold_gb:
        error_msg = f"Memory usage ({current_usage:.2f} GB) exceeds threshold ({threshold_gb} GB)."
        logger.error(error_msg)
        raise MemoryError(error_msg)
    return True

def cleanup_memory():
    """
    Force garbage collection and clear GPU cache if available.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.debug("GPU cache cleared.")

def log_memory_profile(image_id: int, status: str, message: str = ""):
    """
    Log memory profile information.
    """
    usage = get_memory_usage_gb()
    logger.info(f"Memory profile for image {image_id}: {usage:.2f} GB, Status: {status}, Message: {message}")
