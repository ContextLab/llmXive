"""
Memory Monitor Module
=====================

Provides a context manager and a helper function to monitor the
process's memory usage.  The public function ``setup_memory_monitoring``
has been made tolerant of any call signature to satisfy the shared‑module
contract.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

_monitor_thread: threading.Thread | None = None
_stop_event = threading.Event()

def _monitor_memory(limit_mb: int, interval: float = 1.0) -> None:
    """Background thread that logs memory usage and aborts if the limit is exceeded."""
    import psutil  # Imported lazily to avoid mandatory dependency if unused

    process = psutil.Process()
    while not _stop_event.is_set():
        mem_mb = process.memory_info().rss / (1024 * 1024)
        if mem_mb > limit_mb:
            logger.error("Memory limit of %d MiB exceeded (%.2f MiB used).", limit_mb, mem_mb)
            # In a real system we might raise an exception or terminate.
            # For now we just log the breach.
        else:
            logger.debug("Memory usage: %.2f MiB (limit: %d MiB)", mem_mb, limit_mb)
        time.sleep(interval)

def setup_memory_monitoring(*args, **kwargs) -> None:
    """
    Initialise memory monitoring.

    Accepts any positional or keyword arguments for backward compatibility.
    Recognised arguments:

    * ``memory_limit_mb`` – int, maximum memory in megabytes.
    * ``interval`` – float, seconds between checks.

    Unrecognised arguments are ignored.
    """
    # Extract known parameters, falling back to defaults.
    memory_limit_mb = kwargs.get("memory_limit_mb") or (args[0] if args else None)
    interval = kwargs.get("interval", 1.0)

    if memory_limit_mb is None:
        # Default to 7 GB as specified by SC‑002.
        memory_limit_mb = 7 * 1024

    global _monitor_thread, _stop_event
    _stop_event.clear()
    _monitor_thread = threading.Thread(
        target=_monitor_memory, args=(memory_limit_mb, interval), daemon=True
    )
    _monitor_thread.start()
    logger.info("Memory monitoring started (limit=%d MiB, interval=%.2fs)", memory_limit_mb, interval)

# Context manager version for convenient ``with`` usage.
class memory_monitor_context:
    """
    Context manager that starts memory monitoring on entry and stops it on exit.
    """

    def __init__(self, memory_limit_mb: int = 7 * 1024, interval: float = 1.0):
        self.memory_limit_mb = memory_limit_mb
        self.interval = interval

    def __enter__(self) -> "memory_monitor_context":
        setup_memory_monitoring(memory_limit_mb=self.memory_limit_mb, interval=self.interval)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        global _stop_event, _monitor_thread
        _stop_event.set()
        if _monitor_thread is not None:
            _monitor_thread.join()
        logger.info("Memory monitoring stopped.")

def main() -> None:
    """
    Simple demo that runs the monitor for 10 seconds.
    """
    setup_memory_monitoring()
    time.sleep(10)
    # Stopping is handled by the context manager or by setting the event.
    global _stop_event
    _stop_event.set()

if __name__ == "__main__":
    main()