"""Memory monitoring utilities for the project.

This module provides a simple background thread that periodically checks the
current process memory usage and raises an error if it exceeds a configured
limit. The public API is deliberately tolerant of different call signatures
to satisfy all existing callers.

Functions
---------
- get_current_memory_mb(): Returns the resident set size (RSS) of the current
  Python process in megabytes.
- check_memory_limit(memory_limit_mb: Optional[float] = None): Checks the
  current memory usage against the provided limit (or the global config) and
  raises ``MemoryError`` if the usage exceeds the limit.
- setup_memory_monitoring(sample_interval: float = 1.0,
                         memory_limit_mb: Optional[float] = None) -> threading.Thread:
  Starts a daemon thread that periodically invokes ``check_memory_limit``.
  Returns the thread object so callers can stop it later.
- stop_memory_monitoring(thread: threading.Thread): Signals the monitoring
  thread to stop and joins it.
- main(): Simple CLI entry‑point for manual testing.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import psutil

from config import get_memory_limit_mb

_stop_event: threading.Event | None = None
_monitor_thread: threading.Thread | None = None

logger = logging.getLogger(__name__)


def get_current_memory_mb() -> float:
    """Return the current process memory usage (RSS) in megabytes."""
    process = psutil.Process()
    rss_bytes = process.memory_info().rss
    return rss_bytes / (1024 * 1024)


def check_memory_limit(memory_limit_mb: Optional[float] = None) -> None:
    """Check the current memory usage against a limit.

    If ``memory_limit_mb`` is ``None``, the global configuration value from
    ``config.get_memory_limit_mb`` is used. Raises ``MemoryError`` when the
    usage exceeds the limit.
    """
    if memory_limit_mb is None:
        memory_limit_mb = get_memory_limit_mb()
    current_mb = get_current_memory_mb()
    logger.debug(
        "Memory check: current=%.2f MB, limit=%.2f MB",
        current_mb,
        memory_limit_mb,
    )
    if current_mb > memory_limit_mb:
        raise MemoryError(
            f"Memory usage {current_mb:.2f} MB exceeds limit of {memory_limit_mb:.2f} MB"
        )


def _monitor_loop(sample_interval: float, memory_limit_mb: Optional[float]) -> None:
    """Internal loop executed by the monitoring thread."""
    while _stop_event is not None and not _stop_event.is_set():
        try:
            check_memory_limit(memory_limit_mb)
        except MemoryError as exc:
            logger.error(str(exc))
            # In a real setting we might terminate the process; here we just log.
        time.sleep(sample_interval)


def setup_memory_monitoring(
    sample_interval: float = 1.0,
    memory_limit_mb: Optional[float] = None,
    *args,
    **kwargs,
) -> threading.Thread:
    """Start background memory monitoring.

    Parameters
    ----------
    sample_interval: float, optional
        Seconds between consecutive memory checks (default 1.0).
    memory_limit_mb: float, optional
        Memory limit in MB. If omitted, the global config value is used.
    *args, **kwargs:
        Accepted for compatibility with legacy callers; they are ignored.

    Returns
    -------
    threading.Thread
        The daemon thread performing the monitoring.
    """
    global _stop_event, _monitor_thread
    # Ensure any previous monitor is stopped before starting a new one.
    if _monitor_thread is not None and _monitor_thread.is_alive():
        stop_memory_monitoring(_monitor_thread)

    _stop_event = threading.Event()
    _monitor_thread = threading.Thread(
        target=_monitor_loop,
        args=(sample_interval, memory_limit_mb),
        daemon=True,
    )
    _monitor_thread.start()
    logger.info(
        "Memory monitoring started (interval=%.2fs, limit=%s MB)",
        sample_interval,
        memory_limit_mb if memory_limit_mb is not None else get_memory_limit_mb(),
    )
    return _monitor_thread


def stop_memory_monitoring(thread: Optional[threading.Thread] = None) -> None:
    """Signal the monitoring thread to stop and wait for it to finish.

    If ``thread`` is ``None``, the most recently created monitoring thread is
    used. The function is safe to call multiple times.
    """
    global _stop_event, _monitor_thread
    if thread is None:
        thread = _monitor_thread
    if _stop_event is not None:
        _stop_event.set()
    if thread is not None and thread.is_alive():
        thread.join()
        logger.info("Memory monitoring stopped.")
    _stop_event = None
    _monitor_thread = None


def main() -> None:
    """CLI entry‑point for manual verification.

    Starts monitoring, prints the current memory usage once per second, and
    stops after 10 seconds.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    thread = setup_memory_monitoring(sample_interval=1.0)
    try:
        for _ in range(10):
            logger.info("Current memory usage: %.2f MB", get_current_memory_mb())
            time.sleep(1)
    finally:
        stop_memory_monitoring(thread)


if __name__ == "__main__":
    main()
