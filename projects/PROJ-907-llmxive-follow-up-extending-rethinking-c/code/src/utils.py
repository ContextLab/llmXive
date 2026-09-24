import os
import gc
import torch
from typing import Iterable, Iterator, TypeVar
from collections.abc import Sequence
import logging
import json
from pathlib import Path

T = TypeVar('T')

logger = logging.getLogger(__name__)

def batch_iterator(iterable: Iterable[T], batch_size: int) -> Iterator[Sequence[T]]:
    """
    Yields chunks of size `batch_size` from `iterable`.
    """
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.
    """
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated() / (1024 ** 3)
    else:
        # For CPU, we can use psutil if available, otherwise estimate
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            return mem_info.rss / (1024 ** 3)
        except ImportError:
            logger.warning("psutil not available. Returning 0.0 for CPU memory.")
            return 0.0

def memory_guard(threshold_gb: float) -> bool:
    """
    Returns True if current RAM usage < `threshold_gb`, else raises a `MemoryError`.
    """
    current_mem = get_memory_usage_gb()
    if current_mem >= threshold_gb:
        raise MemoryError(f"Current memory usage ({current_mem:.2f} GB) exceeds threshold ({threshold_gb} GB)")
    return True

def cleanup_memory():
    """
    Cleanup unused memory.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def log_memory_profile(log_path: Path, status: str, peak_memory_mb: float, message: str):
    """
    Log memory profile to a JSONL file.
    """
    log_entry = {
        "status": status,
        "peak_memory_mb": peak_memory_mb,
        "message": message,
        "timestamp": os.popen("date").read().strip()
    }
    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    logger.info(f"Memory profile logged: {log_entry}")
