import os
import gc
import torch
from typing import Iterable, Iterator, TypeVar
from collections.abc import Sequence
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')

def batch_iterator(iterable: Iterable[T], batch_size: int) -> Iterator[Sequence[T]]:
    """
    Yields chunks of size `batch_size` from `iterable`.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    
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
    Returns current RAM usage in GB.
    """
    if torch.cuda.is_available():
        # If CUDA is available, we could use torch.cuda.memory_allocated,
        # but the spec implies CPU runner constraints.
        # We use a simple heuristic or psutil if available, else 0.
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_gb = process.memory_info().rss / (1024 ** 3)
            return mem_gb
        except ImportError:
            # Fallback: assume 0 if psutil not available (will not trigger guard)
            # In a real runner, psutil should be present or we use /proc
            if os.path.exists('/proc/self/status'):
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # VmRSS is in kB
                            mem_kb = int(line.split()[1])
                            return mem_kb / (1024 * 1024)
            return 0.0
    else:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_gb = process.memory_info().rss / (1024 ** 3)
            return mem_gb
        except ImportError:
            if os.path.exists('/proc/self/status'):
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            mem_kb = int(line.split()[1])
                            return mem_kb / (1024 * 1024)
            return 0.0

def memory_guard(threshold_gb: float) -> bool:
    """
    Returns True if current RAM usage < `threshold_gb`, else raises a `MemoryError`.
    """
    current_mem = get_memory_usage_gb()
    if current_mem >= threshold_gb:
        raise MemoryError(f"Memory usage {current_mem:.2f}GB exceeds threshold {threshold_gb}GB")
    return True

def cleanup_memory():
    """
    Forces garbage collection and clears CUDA cache if available.
    """
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

def log_memory_profile(mem_gb: float, event: str = "check"):
    """
    Logs memory usage to data/results/memory_profile_raw.jsonl.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "mem_gb": mem_gb
    }
    try:
        with open('data/results/memory_profile_raw.jsonl', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.warning(f"Failed to log memory profile: {e}")
