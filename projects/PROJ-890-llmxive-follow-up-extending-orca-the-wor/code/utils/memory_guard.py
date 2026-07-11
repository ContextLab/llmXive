"""
Memory Guard Utility for Dynamic Batch Size Adjustment.

This module provides utilities to monitor system memory usage via psutil
and dynamically adjust processing batch sizes to prevent OOM errors
during CPU-only inference and training.
"""

import psutil
import logging
from typing import Tuple, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)


def get_available_memory_gb() -> float:
    """
    Returns the currently available system memory in gigabytes.

    Returns:
        float: Available memory in GB.
    """
    mem_info = psutil.virtual_memory()
    # available is in bytes, convert to GB
    return mem_info.available / (1024 ** 3)


def get_memory_usage_percent() -> float:
    """
    Returns the current system memory usage percentage.

    Returns:
        float: Percentage of memory used (0.0 to 100.0).
    """
    mem_info = psutil.virtual_memory()
    return mem_info.percent


def adjust_batch_size(
    current_batch_size: int,
    min_batch_size: int = 1,
    max_batch_size: int = 64,
    target_usage_percent: float = 80.0,
    safety_margin: float = 0.9
) -> int:
    """
    Dynamically adjusts the batch size based on current system memory usage.

    This function estimates the memory pressure and scales the batch size down
    if usage is high, or allows it to stay up to the maximum if memory is plentiful.

    Args:
        current_batch_size: The proposed or current batch size.
        min_batch_size: The absolute minimum batch size allowed (default 1).
        max_batch_size: The maximum allowed batch size (default 64).
        target_usage_percent: The memory usage threshold above which we reduce batch size.
        safety_margin: A multiplier applied to available memory to be conservative.

    Returns:
        int: The adjusted batch size.
    """
    current_usage = get_memory_usage_percent()
    available_gb = get_available_memory_gb()

    logger.debug(
        f"Memory check: Usage={current_usage:.1f}%, "
        f"Available={available_gb:.2f}GB, CurrentBatch={current_batch_size}"
    )

    # If memory usage is below the target threshold, we can try to use the max batch size
    # or keep the current one if it's already reasonable.
    if current_usage < target_usage_percent:
        # If we have plenty of memory, allow up to max_batch_size
        # Heuristic: if usage is very low (< 50%), allow max.
        if current_usage < 50.0:
            new_batch = max_batch_size
        else:
            # Linear interpolation between min and max based on how close we are to target
            # At 50% -> max, at target -> min (roughly)
            ratio = (target_usage_percent - current_usage) / (target_usage_percent - 50.0)
            new_batch = int(min_batch_size + ratio * (max_batch_size - min_batch_size))
            new_batch = max(min_batch_size, min(new_batch, max_batch_size))
    else:
        # Memory is high, reduce batch size aggressively
        # Calculate a reduction factor based on how far over the limit we are
        excess = current_usage - target_usage_percent
        reduction_factor = max(0.1, 1.0 - (excess / 20.0)) # Reduce by up to 90% if 20% over
        
        new_batch = int(current_batch_size * reduction_factor)
        new_batch = max(min_batch_size, min(new_batch, max_batch_size))

    # Ensure we don't go below min or above max
    new_batch = max(min_batch_size, min(new_batch, max_batch_size))

    if new_batch != current_batch_size:
        logger.info(
            f"Adjusted batch size from {current_batch_size} to {new_batch} "
            f"(Current Memory Usage: {current_usage:.1f}%)"
        )
    else:
        logger.debug(f"Batch size remains {new_batch} (Current Memory Usage: {current_usage:.1f}%)")

    return new_batch


def check_memory_sufficient(
    required_gb: float,
    safety_factor: float = 1.2
) -> Tuple[bool, float]:
    """
    Checks if the system has enough available memory for a specific requirement.

    Args:
        required_gb: The amount of memory required in GB.
        safety_factor: A multiplier to ensure we don't use all available memory.

    Returns:
        Tuple[bool, float]: (is_sufficient, available_gb)
    """
    available_gb = get_available_memory_gb()
    required_with_safety = required_gb * safety_factor
    return (available_gb >= required_with_safety), available_gb
