import os
import gc
import torch
from typing import Iterable, Iterator, TypeVar
from collections.abc import Sequence
import logging

logger = logging.getLogger(__name__)

def batch_iterator(iterable: Iterable, batch_size: int) -> Iterator:
    """Yield chunks of size `batch_size` from `iterable`."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def memory_guard(threshold_gb: float) -> bool:
    """
    Check if current RAM usage is below threshold.
    Returns True if safe, else raises MemoryError.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_usage_gb = process.memory_info().rss / (1024 ** 3)
        if mem_usage_gb >= threshold_gb:
            raise MemoryError(f"Memory usage {mem_usage_gb:.2f} GB exceeds threshold {threshold_gb} GB")
        return True
    except ImportError:
        logger.warning("psutil not found. Skipping memory guard check.")
        return True
    except Exception as e:
        logger.error(f"Memory guard check failed: {e}")
        raise