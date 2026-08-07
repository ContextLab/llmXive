"""
memory_guard.py

Utility for monitoring and managing memory usage during processing.
Dynamically adjusts batch sizes based on available memory.
"""

import psutil
import logging
from typing import Tuple, Optional
from config import MAX_MEMORY_GB, MEMORY_WARNING_THRESHOLD, MEMORY_CRITICAL_THRESHOLD

logger = logging.getLogger(__name__)

def get_available_memory_gb() -> float:
    """Returns available memory in GB."""
    mem = psutil.virtual_memory()
    return mem.available / (1024 ** 3)

def get_memory_usage_percent() -> float:
    """Returns current memory usage as a percentage."""
    mem = psutil.virtual_memory()
    return mem.percent

def check_memory_sufficient(min_required_gb: float = 2.0) -> bool:
    """Checks if sufficient memory is available."""
    available = get_available_memory_gb()
    return available >= min_required_gb

def adjust_batch_size(current_usage_percent: float, threshold: float = 90) -> int:
    """
    Adjusts batch size based on current memory usage.
    Reduces batch size if usage exceeds threshold.

    Args:
        current_usage_percent: Current memory usage percentage.
        threshold: Threshold above which to reduce batch size.

    Returns:
        int: New suggested batch size.
    """
    from config import MAX_BATCH_SIZE

    if current_usage_percent < threshold:
        return MAX_BATCH_SIZE

    # Reduce batch size by half, minimum 1
    new_size = max(1, MAX_BATCH_SIZE // 2)
    logger.warning(f"Memory usage {current_usage_percent}% exceeds threshold {threshold}%. Reducing batch size to {new_size}.")

    # Further reduction if still high
    if current_usage_percent > 95:
        new_size = max(1, new_size // 2)
        logger.warning(f"Memory usage critical {current_usage_percent}%. Further reducing batch size to {new_size}.")

    return new_size
