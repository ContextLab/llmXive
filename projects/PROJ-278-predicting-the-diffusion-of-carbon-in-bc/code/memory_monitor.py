"""Memory monitoring utilities."""
import psutil
import os
import atexit
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_process = psutil.Process(os.getpid())
_peak_memory_mb = 0.0

def update_peak_memory():
    """Update peak memory usage."""
    global _peak_memory_mb
    current = _process.memory_info().rss / 1024 / 1024
    if current > _peak_memory_mb:
        _peak_memory_mb = current

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    return _peak_memory_mb

def reset_peak_memory():
    """Reset peak memory tracking."""
    global _peak_memory_mb
    _peak_memory_mb = 0.0

def log_peak_memory(stage: str):
    """Log peak memory at a specific stage."""
    update_peak_memory()
    logger.info(f"Peak memory at {stage}: {_peak_memory_mb:.2f} MB")

def final_log():
    """Final log of peak memory."""
    update_peak_memory()
    logger.info(f"Final peak memory: {_peak_memory_mb:.2f} MB")

atexit.register(final_log)

monitor_memory_interval = 1.0
