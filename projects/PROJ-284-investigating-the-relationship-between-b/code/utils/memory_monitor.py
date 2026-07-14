"""Memory profiling and dynamic batch sizing utility."""
from __future__ import annotations

import os
import sys
from typing import Optional, Tuple
import psutil
from code.logging_config import get_logger

logger = get_logger(__name__)

# Constants
MEMORY_LIMIT_GB = 7.0  # Default memory limit in GB


def get_available_memory(GB: float = MEMORY_LIMIT_GB) -> int:
    """Get available system memory in bytes.

    Args:
        GB: The memory limit in GB to use as a reference.

    Returns:
        Available memory in bytes (limited by the GB parameter).
    """
    try:
        mem = psutil.virtual_memory()
        available_bytes = mem.available
        limit_bytes = int(GB * 1024**3)
        return min(available_bytes, limit_bytes)
    except Exception as e:
        logger.log("get_available_memory", error=str(e), fallback=1024**3 * 2)
        return int(GB * 1024**3)


def estimate_memory_usage(num_rows: int, num_cols: int, dtype_size: int = 8) -> int:
    """Estimate memory usage for a DataFrame-like structure.

    Args:
        num_rows: Number of rows.
        num_cols: Number of columns.
        dtype_size: Size of each element in bytes (default 8 for float64).

    Returns:
        Estimated memory usage in bytes.
    """
    # Base estimate: rows * cols * dtype_size
    # Add 20% overhead for pandas structure
    base = num_rows * num_cols * dtype_size
    return int(base * 1.2)


def calculate_batch_size(
    total_items: int,
    item_memory_estimate: int,
    max_memory_bytes: Optional[int] = None
) -> int:
    """Calculate optimal batch size to stay within memory limits.

    Args:
        total_items: Total number of items to process.
        item_memory_estimate: Estimated memory usage per item in bytes.
        max_memory_bytes: Maximum memory to use (bytes). If None, uses default limit.

    Returns:
        Optimal batch size (number of items per batch).
    """
    if max_memory_bytes is None:
        max_memory_bytes = get_available_memory()

    if item_memory_estimate == 0:
        return total_items

    # Calculate how many items fit in memory
    # Use 90% of available memory for safety
    safe_memory = max_memory_bytes * 0.9
    batch_size = int(safe_memory // item_memory_estimate)

    if batch_size < 1:
        batch_size = 1
    if batch_size > total_items:
        batch_size = total_items

    logger.log(
        "calculate_batch_size",
        total_items=total_items,
        item_memory_bytes=item_memory_estimate,
        max_memory_bytes=max_memory_bytes,
        batch_size=batch_size
    )
    return batch_size