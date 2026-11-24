"""
Resource‑guard utilities for the pipeline.

The original ``openneuro_fetcher`` expected a ``utils.resource_guard``
module providing ``enforce_memory_limit``.  During the V02 implementation
this module was omitted, causing import errors that prevented the entire
pipeline (including the preprocessing step) from executing.

This lightweight implementation offers a single function that checks the
current RAM usage and raises ``MemoryError`` if a configurable threshold
is exceeded.  It deliberately keeps the behaviour simple – the pipeline
already contains a more sophisticated ``memory_monitor`` module – but
satisfies the import contract and provides a useful safety net.
"""

import logging
import os
from pathlib import Path

import psutil

from llmxive_toolkit import get_logger

logger = get_logger(__name__)

def enforce_memory_limit(max_memory_gb: float = 6.0) -> None:
    """
    Raise ``MemoryError`` if the current process exceeds ``max_memory_gb``.

    Args:
        max_memory_gb: Maximum allowed resident memory in gigabytes.

    Raises:
        MemoryError: If the process's RSS exceeds the limit.
    """
    process = psutil.Process(os.getpid())
    rss_bytes = process.memory_info().rss
    rss_gb = rss_bytes / (1024 ** 3)

    if rss_gb > max_memory_gb:
        msg = (
            f"Memory usage ({rss_gb:.2f} GB) exceeds the allowed limit of "
            f"{max_memory_gb:.2f} GB.  The pipeline aborts to avoid OOM."
        )
        logger.error(msg)
        raise MemoryError(msg)
    else:
        logger.debug(f"Memory usage OK: {rss_gb:.2f} GB / {max_memory_gb:.2f} GB limit.")