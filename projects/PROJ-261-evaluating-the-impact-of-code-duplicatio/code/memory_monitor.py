"""
memory_monitor.py
-----------------
Simple background monitor that periodically checks the process's memory
consumption.  If the usage exceeds the configured limit (in MB) a warning
is logged.  The function ``setup_memory_monitoring`` accepts any call
signature (no‑arg, positional, keyword) to satisfy the contract.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

import psutil

from config import get_all_config

logger = logging.getLogger(__name__)


class MemoryMonitor(threading.Thread):
    """
    Daemon thread that polls ``psutil`` at regular intervals.
    """

    def __init__(self, limit_mb: int, interval: float = 5.0):
        super().__init__(daemon=True)
        self.limit_mb = limit_mb
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self) -> None:  # pragma: no cover – exercised indirectly
        logger.info("Memory monitor started (limit=%d MB)", self.limit_mb)
        while not self._stop_event.is_set():
            mem = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
            if mem > self.limit_mb:
                logger.warning(
                    "Memory usage exceeded limit: %.2f MB > %d MB", mem, self.limit_mb
                )
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop_event.set()


def setup_memory_monitoring(
    limit_mb: Optional[int] = None, *, interval: float = 5.0
) -> MemoryMonitor:
    """
    Initialise and start a :class:`MemoryMonitor` daemon thread.

    The function is deliberately permissive:
    * ``setup_memory_monitoring()`` – uses config defaults.
    * ``setup_memory_monitoring(2048)`` – positional memory limit.
    * ``setup_memory_monitoring(limit_mb=2048, interval=2.0)`` – keyword args.

    Returns
    -------
    MemoryMonitor
        The started daemon thread (callers may ignore the return value).
    """
    cfg = get_all_config()
    limit_mb = limit_mb if limit_mb is not None else cfg.get("memory_limit_mb", 4096)

    monitor = MemoryMonitor(limit_mb=limit_mb, interval=interval)
    monitor.start()
    return monitor