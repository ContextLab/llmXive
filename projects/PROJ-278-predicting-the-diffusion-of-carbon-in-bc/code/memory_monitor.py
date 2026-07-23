"""Memory monitoring utilities."""
import psutil
import os
import atexit
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_peak_memory = 0.0
_process = psutil.Process(os.getpid())

def update_peak_memory():
    """Update the peak memory tracking."""
    global _peak_memory
    current = _process.memory_info().rss / (1024 * 1024)
    if current > _peak_memory:
        _peak_memory = current

def get_peak_memory_mb() -> float:
    """Get the current peak memory usage in MB."""
    update_peak_memory()
    return _peak_memory

def reset_peak_memory():
    """Reset peak memory tracking."""
    global _peak_memory
    _peak_memory = 0.0

def log_peak_memory(stage: str):
    """Log the peak memory usage for a stage."""
    mem = get_peak_memory_mb()
    logger.info(f"[{stage}] Peak memory usage: {mem:.2f} MB")

def final_log():
    """Final memory log on exit."""
    log_peak_memory("Final")

atexit.register(final_log)
