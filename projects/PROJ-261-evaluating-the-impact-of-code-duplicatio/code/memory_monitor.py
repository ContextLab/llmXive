"""
memory_monitor.py
-----------------
Simple memory‑monitoring utility. The ``setup_memory_monitoring`` function
now accepts ``*args, **kwargs`` so that all callers (including future
extensions) can pass parameters without causing import‑time crashes.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

_monitor_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()

def _monitor(memory_limit_mb: int, interval: float) -> None:
    """Background thread that checks process memory usage."""
    import psutil  # Imported lazily to avoid hard dependency when unused.

    while not _stop_event.is_set():
        usage = psutil.Process().memory_info().rss / (1024 * 1024)
        if usage > memory_limit_mb:
            logger.warning(
                "Memory usage %.2f MB exceeded limit of %d MB", usage, memory_limit_mb
            )
        time.sleep(interval)

def setup_memory_monitoring(*args, **kwargs) -> None:
    """
    Start a background thread that monitors memory usage.

    Accepted parameters (all optional):
    * ``memory_limit_mb`` – int – default 7000
    * ``interval`` – float – seconds between checks, default 5.0
    """
    memory_limit_mb = kwargs.get("memory_limit_mb", 7000)
    interval = kwargs.get("interval", 5.0)

    global _monitor_thread
    if _monitor_thread and _monitor_thread.is_alive():
        logger.debug("Memory monitor already running")
        return

    _stop_event.clear()
    _monitor_thread = threading.Thread(
        target=_monitor, args=(memory_limit_mb, interval), daemon=True
    )
    _monitor_thread.start()
    logger.info(
        "Memory monitoring started (limit=%d MB, interval=%.1f s)",
        memory_limit_mb,
        interval,
    )

@contextmanager
def memory_monitor_context(*args, **kwargs):
    """Convenient context manager that starts and stops monitoring."""
    try:
        setup_memory_monitoring(*args, **kwargs)
        yield
    finally:
        _stop_event.set()
        if _monitor_thread:
            _monitor_thread.join()
