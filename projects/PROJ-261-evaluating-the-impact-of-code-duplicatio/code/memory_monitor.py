"""
memory_monitor.py
-----------------
Simple background thread that periodically checks the process's RSS memory
usage and logs a warning if it exceeds a configured limit.
"""

from __future__ import annotations
import logging
import threading
import time
from typing import Optional

import psutil

logger = logging.getLogger(__name__)


class MemoryMonitor(threading.Thread):
    """
    Daemon thread that monitors the current process memory usage.
    """

    def __init__(self, memory_limit_mb: int = 7_000, interval: float = 5.0):
        super().__init__(daemon=True)
        self.memory_limit_mb = memory_limit_mb
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            rss_mb = psutil.Process().memory_info().rss / (1024 * 1024)
            if rss_mb > self.memory_limit_mb:
                logger.warning(
                    "Memory usage %.2f MiB exceeds limit of %d MiB",
                    rss_mb,
                    self.memory_limit_mb,
                )
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop_event.set()


def setup_memory_monitoring(
    memory_limit_mb: int = 7_000,
    interval: float = 5.0,
    **_: any,
) -> MemoryMonitor:
    """
    Initialise and start a :class:`MemoryMonitor` in the background.

    This function accepts flexible arguments so that older call‑sites that
    pass positional arguments or extra keywords continue to work.
    """
    monitor = MemoryMonitor(memory_limit_mb=memory_limit_mb, interval=interval)
    monitor.start()
    logger.debug(
        "Memory monitor started (limit=%d MiB, interval=%.1fs)",
        memory_limit_mb,
        interval,
    )
    return monitor