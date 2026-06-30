"""
memory_monitor.py
-----------------
Minimal memory‑monitoring utility. The original implementation accepted a
``memory_limit_mb`` argument and an ``interval`` argument, but many call‑sites
invoke it with no parameters. The updated version therefore provides a
flexible signature that works with all existing usages.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Generator, Optional

from .config import get_memory_limit_mb

logger = logging.getLogger(__name__)

__all__ = ["setup_memory_monitoring", "memory_monitor_context", "main"]


def _monitor_memory(limit_mb: int, interval: float, stop_event: threading.Event) -> None:
    """
    Background thread that periodically logs current memory usage.
    In this lightweight implementation we only log a placeholder message
    because accurate cross‑platform memory measurement would add unnecessary
    dependencies.
    """
    logger.debug("Memory monitor started – limit %d MB, interval %.2fs", limit_mb, interval)
    while not stop_event.is_set():
        # Placeholder – in a real system you would query the process RSS.
        logger.debug("Memory usage check (placeholder)")
        time.sleep(interval)
    logger.debug("Memory monitor stopped")


def setup_memory_monitoring(
    memory_limit_mb: Optional[int] = None,
    interval: float = 5.0,
    *args,
    **kwargs,
) -> None:
    """
    Start a background thread that pretends to monitor memory usage.

    Parameters are optional so that the function can be called as:

    * ``setup_memory_monitoring()`` – uses defaults from ``code.config``.
    * ``setup_memory_monitoring(memory_limit_mb=..., interval=...)``
    * ``setup_memory_monitoring`` with any extra ``*args``/``**kwargs`` that
      older call‑sites may supply.

    The thread runs as a daemon and will not prevent interpreter shutdown.
    """
    # Resolve defaults if not explicitly provided.
    if memory_limit_mb is None:
        memory_limit_mb = get_memory_limit_mb()

    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=_monitor_memory,
        args=(memory_limit_mb, interval, stop_event),
        daemon=True,
    )
    monitor_thread.start()
    logger.info(
        "Memory monitoring started (limit=%d MB, interval=%.2fs)", memory_limit_mb, interval
    )
    # Store the stop event on the thread object so callers could stop it later
    # if they really need to (not used elsewhere in this project).
    monitor_thread.stop_event = stop_event  # type: ignore[attr-defined]


# ----------------------------------------------------------------------
# Context‑manager version – retained for compatibility with any existing
# imports that expect ``memory_monitor_context``.
# ----------------------------------------------------------------------
from contextlib import contextmanager


@contextmanager
def memory_monitor_context(
    memory_limit_mb: Optional[int] = None,
    interval: float = 5.0,
) -> Generator[None, None, None]:
    """
    Context manager that starts the monitor on entry and stops it on exit.
    """
    stop_event = threading.Event()
    limit = memory_limit_mb or get_memory_limit_mb()
    thread = threading.Thread(
        target=_monitor_memory,
        args=(limit, interval, stop_event),
        daemon=True,
    )
    thread.start()
    try:
        yield
    finally:
        stop_event.set()
        thread.join()
        logger.debug("Memory monitor context exited")


def main() -> None:
    """
    Simple demo that starts the monitor for a short period.
    """
    logging.basicConfig(level=logging.INFO)
    setup_memory_monitoring()
    # Run for a few seconds then exit.
    time.sleep(2)
    logger.info("Demo memory monitor finished")