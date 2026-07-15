import os
import gc
import torch
from typing import Iterable, Iterator, TypeVar
from collections.abc import Sequence
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

def batch_iterator(iterable: Iterable[T], batch_size: int) -> Iterator[Sequence[T]]:
    """
    Yields chunks of size `batch_size` from `iterable`.
    
    Args:
        iterable: The input iterable.
        batch_size: The size of each batch.
    
    Yields:
        A list (or sequence) of items of size `batch_size`.
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def _get_memory_usage_gb() -> float:
    """
    Returns current memory usage in GB.
    Tries to read from /proc/self/status on Linux, falls back to 0.0.
    """
    try:
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / 1e9
        else:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        rss_kb = int(line.split()[1])
                        return rss_kb / 1e6
    except (FileNotFoundError, IndexError, ValueError):
        return 0.0

def memory_guard(threshold_gb: float) -> bool:
    """
    Checks if current RAM usage is below the threshold.
    
    Args:
        threshold_gb: The memory threshold in GB.
    
    Returns:
        True if current RAM usage < threshold_gb.
    
    Raises:
        MemoryError: If current RAM usage >= threshold_gb.
    """
    current_usage = _get_memory_usage_gb()
    if current_usage >= threshold_gb:
        logger.warning(f"Memory usage {current_usage:.2f} GB exceeds threshold {threshold_gb} GB.")
        raise MemoryError(f"Memory usage {current_usage:.2f} GB exceeds threshold {threshold_gb} GB.")
    return True
