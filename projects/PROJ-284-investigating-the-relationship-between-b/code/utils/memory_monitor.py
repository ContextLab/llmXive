"""Memory profiling and dynamic batch sizing utilities."""
from __future__ import annotations

import os
import sys
from typing import Optional, Tuple

import psutil

from code.logging_config import get_logger

logger = get_logger(__name__)


def get_available_memory() -> int:
    """
    Returns the available memory in bytes.

    Uses psutil to query system memory. Falls back to total memory if
    available memory is not reported (e.g., on some Windows configurations).
    """
    mem = psutil.virtual_memory()
    available = mem.available
    if available is None or available <= 0:
        available = mem.total
    logger.log("get_available_memory", available_bytes=available)
    return int(available)


def estimate_memory_usage(df_rows: int, df_cols: int, dtype_bytes: int = 8) -> int:
    """
    Estimates memory usage for a DataFrame in bytes.

    Args:
        df_rows: Number of rows.
        df_cols: Number of columns.
        dtype_bytes: Bytes per element (default 8 for float64).

    Returns:
        Estimated memory usage in bytes.
    """
    estimated = df_rows * df_cols * dtype_bytes
    logger.log("estimate_memory_usage", rows=df_rows, cols=df_cols, dtype_bytes=dtype_bytes, estimated_bytes=estimated)
    return estimated


def calculate_batch_size(
    target_memory_fraction: float = 0.7,
    min_batch: int = 10,
    max_batch: Optional[int] = None
) -> int:
    """
    Calculates a safe batch size based on available memory.

    Args:
        target_memory_fraction: Fraction of available memory to target.
        min_batch: Minimum batch size to return.
        max_batch: Maximum batch size cap.

    Returns:
        Safe batch size integer.
    """
    available = get_available_memory()
    target_bytes = int(available * target_memory_fraction)

    # Heuristic: Assume a batch of 100 subjects with 400x400 matrices (float64)
    # 400x400x8 = 1,280,000 bytes per subject matrix
    # Plus overhead for metadata/DFs ~ 20%
    bytes_per_subject = 1280000 * 1.2

    if bytes_per_subject <= 0:
        return min_batch

    batch = int(target_bytes / bytes_per_subject)
    batch = max(min_batch, batch)

    if max_batch is not None:
        batch = min(batch, max_batch)

    logger.log("calculate_batch_size", available_bytes=available, target_bytes=target_bytes, result=batch)
    return batch
