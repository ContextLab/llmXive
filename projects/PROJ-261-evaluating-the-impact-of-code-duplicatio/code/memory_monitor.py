from __future__ import annotations

import logging
import os
import threading
import time
from contextlib import contextmanager
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

__all__ = [
    "setup_memory_monitoring",
    "memory_monitor_context",
    "memory_monitor_thread",
]


def _monitor_memory(limit_bytes: int, interval: float, stop_event: threading.Event) -> None:
    """
    Background thread target that periodically checks the current process RSS memory.
    If the memory usage exceeds ``limit_bytes`` a ``MemoryError`` is raised,
    which will terminate the program (the exception propagates to the main thread
    when the thread is joined).
    """
    process = psutil.Process(os.getpid())
    while not stop_event.is_set():
        try:
            mem = process.memory_info().rss
            if mem > limit_bytes:
                logger.error(
                    f"Memory usage exceeded limit: {mem / 1e6:.2f} MB > {limit_bytes / 1e6:.2f} MB"
                )
                # Raising here will be caught by the join in the context manager
                raise MemoryError(
                    f"Memory limit of {limit_bytes} bytes exceeded (current: {mem} bytes)"
                )
        except Exception as exc:  # pragma: no cover – defensive
            logger.exception("Unexpected error in memory monitor thread: %s", exc)
        time.sleep(interval)


def setup_memory_monitoring(
    memory_limit_mb: Optional[int] = None, interval: float = 1.0
) -> tuple[threading.Event, threading.Thread]:
    """
    Start a daemon thread that monitors the current process memory usage.

    Parameters
    ----------
    memory_limit_mb: int | None
        The memory limit in megabytes. If ``None`` the value is obtained from
        :func:`code.config.get_memory_limit_mb`. The default for this project
        (SC‑002) is 7 GB (7 240 MB).
    interval: float
        How often, in seconds, the memory usage is sampled.

    Returns
    -------
    stop_event: threading.Event
        An event that can be set to request the monitor to stop.
    thread: threading.Thread
        The daemon thread that performs the monitoring.
    """
    from code.config import get_memory_limit_mb

    if memory_limit_mb is None:
        memory_limit_mb = get_memory_limit_mb()
    limit_bytes = memory_limit_mb * 1024 * 1024

    stop_event = threading.Event()
    thread = threading.Thread(
        target=_monitor_memory,
        args=(limit_bytes, interval, stop_event),
        daemon=True,
        name="MemoryMonitorThread",
    )
    thread.start()
    logger.info(
        f"Memory monitor started – limit: {memory_limit_mb} MB, interval: {interval}s"
    )
    return stop_event, thread


@contextmanager
def memory_monitor_context(
    memory_limit_mb: Optional[int] = None, interval: float = 1.0
):
    """
    Context manager that activates memory monitoring for the duration of the
    ``with`` block.

    Example
    -------
    >>> from code.memory_monitor import memory_monitor_context
    >>> with memory_monitor_context():
    ...     # model inference or any heavy computation
    ...     run_model()
    """
    stop_event, thread = setup_memory_monitoring(memory_limit_mb, interval)
    try:
        yield
    finally:
        # Signal the thread to stop and wait briefly for a clean shutdown.
        stop_event.set()
        thread.join(timeout=2.0)
        logger.info("Memory monitor stopped")
