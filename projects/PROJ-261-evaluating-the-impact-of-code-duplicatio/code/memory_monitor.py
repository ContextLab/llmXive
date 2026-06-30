"""Utility for monitoring memory usage during long‑running steps.

The original ``setup_memory_monitoring`` function accepted no arguments.
The pipeline now calls it without arguments, but other callers may pass
arbitrary ``*args``/``**kwargs``.  To keep the public contract stable we
extend the signature accordingly while preserving the original behaviour.
"""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

_monitor_thread: Optional[threading.Thread] = None
_stop_event: Optional[threading.Event] = None

def start_memory_monitoring(limit_mb: int = 7 * 1024) -> None:
    """Background thread that periodically checks the process memory usage.

    If the usage exceeds *limit_mb* a warning is emitted.  The function
    returns immediately; the thread runs until :func:`stop_memory_monitoring`
    is called.
    """
    import psutil  # Imported lazily to avoid a hard dependency for callers that don't need it.

    def _monitor():
        while not _stop_event.is_set():
            mem = psutil.Process().memory_info().rss / (1024 * 1024)
            if mem > limit_mb:
                logger.warning("Memory usage %.1f MiB exceeds limit of %d MiB", mem, limit_mb)
            time.sleep(1)

    global _monitor_thread, _stop_event
    if _monitor_thread and _monitor_thread.is_alive():
        logger.debug("Memory monitor already running.")
        return

    _stop_event = threading.Event()
    _monitor_thread = threading.Thread(target=_monitor, daemon=True)
    _monitor_thread.start()
    logger.debug("Memory monitor started with limit %d MiB.", limit_mb)

def stop_memory_monitoring() -> None:
    """Signal the monitoring thread to stop and wait for it to finish."""
    global _monitor_thread, _stop_event
    if _stop_event:
        _stop_event.set()
    if _monitor_thread:
        _monitor_thread.join()
    logger.debug("Memory monitor stopped.")

@contextmanager
def memory_monitor_context():
    """Context manager that starts the monitor on entry and stops it on exit."""
    start_memory_monitoring()
    try:
        yield
    finally:
        stop_memory_monitoring()

# --------------------------------------------------------------------------- #
# Compatibility wrapper – accepts any arguments to stay tolerant.
# --------------------------------------------------------------------------- #
def setup_memory_monitoring(*args, **kwargs) -> None:
    """Compatibility wrapper for legacy callers.

    The original implementation expected no arguments.  This wrapper forwards
    all received arguments to :func:`start_memory_monitoring`, allowing the
    function to be called with arbitrary ``*args``/``**kwargs`` without
    breaking existing code.
    """
    logger.debug("setup_memory_monitoring called with args=%s kwargs=%s", args, kwargs)
    # ``start_memory_monitoring`` already has sensible defaults.
    start_memory_monitoring(*args, **kwargs)
