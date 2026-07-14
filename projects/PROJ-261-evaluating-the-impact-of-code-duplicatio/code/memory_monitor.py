"""memory_monitor.py
Simple memory‑usage monitor that can be invoked with any signature.
The function is tolerant of extra positional and keyword arguments
to satisfy the shared‑module contract.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _monitor(limit_mb: int, interval: float = 1.0) -> None:
    """Internal helper that logs a warning if memory usage exceeds ``limit_mb``."""
    try:
        import psutil
    except ImportError:
        logger.warning("psutil not installed – memory monitoring disabled.")
        return

    while True:
        mem = psutil.Process().memory_info().rss / (1024 * 1024)
        if mem > limit_mb:
            logger.warning(
                "Memory usage exceeded limit: %.2f MB > %d MB", mem, limit_mb
            )
        time.sleep(interval)


def setup_memory_monitoring(*args: Any, **kwargs: Any) -> None:
    """
    Public entry point used throughout the pipeline.

    Accepts any arguments to stay compatible with callers that may
    provide configuration values. The function extracts ``memory_limit_mb``
    from the keyword arguments if present; otherwise it falls back to a
    default of 7 GB.
    """
    limit_mb: int = kwargs.get("memory_limit_mb", 7 * 1024)

    logger.info("Starting memory monitor with limit %d MB", limit_mb)
    thread = threading.Thread(target=_monitor, args=(limit_mb,), daemon=True)
    thread.start()