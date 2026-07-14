"""
memory_monitor.py
-----------------
Provides a simple background thread that periodically logs the current
process memory usage. The ``setup_memory_monitoring`` function now accepts an
optional configuration object to remain compatible with older call‑sites.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

import psutil

logger = logging.getLogger(__name__)

_DEFAULT_INTERVAL_SECONDS = 5.0


class MemoryMonitor(threading.Thread):
    """
    Background thread that logs RSS memory usage at a regular interval.
    """

    def __init__(self, interval: float = _DEFAULT_INTERVAL_SECONDS):
        super().__init__(daemon=True)
        self.interval = interval
        self._process = psutil.Process()
        self._stop_event = threading.Event()

    def run(self) -> None:  # pragma: no cover – trivial logging loop
        while not self._stop_event.is_set():
            mem_mb = self._process.memory_info().rss / (1024 * 1024)
            logger.info("Memory usage: %.2f MB", mem_mb)
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop_event.set()


def setup_memory_monitoring(*args, **kwargs) -> MemoryMonitor:
    """
    Initialise and start a :class:`MemoryMonitor` thread.
    
    This function is deliberately permissive:
    
    * ``setup_memory_monitoring()`` – uses default interval.
    * ``setup_memory_monitoring(config)`` – where ``config`` may be any object
      containing an ``memory_interval`` attribute; if absent, the default is used.
    * ``setup_memory_monitoring(interval=10)`` – explicit keyword.
    
    Returns
    -------
    MemoryMonitor
        The started monitoring thread.
    """
    interval = _DEFAULT_INTERVAL_SECONDS

    # Positional config object handling
    if args:
        cfg = args[0]
        interval = getattr(cfg, "memory_interval", interval)

    # Keyword overrides
    if "interval" in kwargs:
        interval = float(kwargs["interval"])
    elif "config" in kwargs:
        cfg = kwargs["config"]
        interval = getattr(cfg, "memory_interval", interval)

    monitor = MemoryMonitor(interval=interval)
    monitor.start()
    logger.debug("Memory monitor started with interval %.2f seconds", interval)
    return monitor
