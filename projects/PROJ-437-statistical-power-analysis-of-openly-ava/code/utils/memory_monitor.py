"""
Memory Monitor Utility.

Provides a simple function to check available system memory and raise an error
if the available memory falls below a configurable threshold. This is used by
the pipeline to enforce the "fail‑loudly" policy: the pipeline should abort
rather than silently continue with insufficient resources.
"""

import logging
import os
from pathlib import Path

import psutil

logger = logging.getLogger(__name__)

# Default threshold: 75 % of total RAM must be free.
DEFAULT_FREE_MEMORY_RATIO = 0.75

def monitor_and_ensure_memory(min_free_ratio: float = DEFAULT_FREE_MEMORY_RATIO) -> None:
    """
    Verify that a sufficient fraction of system memory is free.

    Args:
        min_free_ratio: Minimum proportion of total memory that must be free
                        (e.g., 0.75 means at least 75 % free).

    Raises:
        MemoryError: If the free memory ratio is below ``min_free_ratio``.
    """
    vm = psutil.virtual_memory()
    free_ratio = vm.available / vm.total
    logger.debug(
        f"Memory check – total: {vm.total / (1024**3):.2f} GB, "
        f"available: {vm.available / (1024**3):.2f} GB, "
        f"free_ratio: {free_ratio:.2%}"
    )
    if free_ratio < min_free_ratio:
        raise MemoryError(
            f"Insufficient free memory: {free_ratio:.2%} available, "
            f"required >= {min_free_ratio:.2%}"
        )
    else:
        logger.info(
            f"Sufficient memory available ({free_ratio:.2%} free)."
        )
