import os
import gc
import torch
from typing import Iterable, Iterator, TypeVar
from collections.abc import Sequence
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

T = TypeVar('T')

def batch_iterator(iterable: Iterable[T], batch_size: int) -> Iterator[list]:
    """Yields chunks of size `batch_size` from `iterable`."""
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def get_memory_usage_gb() -> float:
    """Returns current RAM usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.pid)
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed. Estimating memory usage from torch.")
        if torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 3)
        else:
            # Fallback: estimate based on available memory
            # This is a rough estimate and may not be accurate
            return 2.0  # Default estimate

def memory_guard(threshold_gb: float) -> bool:
    """
    Returns True if current RAM usage < `threshold_gb`, else raises a `MemoryError` exception.
    """
    current_mem = get_memory_usage_gb()
    if current_mem >= threshold_gb:
        raise MemoryError(f"Memory usage ({current_mem:.2f}GB) exceeds threshold ({threshold_gb}GB)")
    return True

def cleanup_memory():
    """Cleans up unused memory."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def log_memory_profile(log_file, memory_gb: float, level: str):
    """Logs memory profile to a JSON lines file."""
    import json
    import time
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "memory_gb": memory_gb,
        "level": level
    }
    log_file.write(json.dumps(entry) + "\n")
    log_file.flush()
