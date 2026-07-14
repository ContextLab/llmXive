"""
memory_monitor.py
-----------------
Simple background monitor that periodically logs the process's memory usage.
The monitor can be started with or without an explicit configuration object.
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
    Daemon thread that logs resident memory usage every ``interval`` seconds.
    """
    def __init__(self, interval: float = 5.0):
        super().__init__(daemon=True)
        self.interval = interval
        self._process = psutil.Process()
        self._stop_event = threading.Event()

    def run(self) -> None:  # pragma: no cover
        logger.info("Memory monitor started (interval=%.1fs).", self.interval)
        while not self._stop_event.is_set():
            mem = self._process.memory_info().rss / (1024 ** 2)  # MB
            logger.debug("Current RSS memory usage: %.2f MB", mem)
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop_event.set()

def setup_memory_monitoring(config: Optional[Mapping[str, Any]] = None) -> MemoryMonitor:
    """
    Initialise and start a :class:`MemoryMonitor`.

    Parameters
    ----------
    config : optional mapping
        Legacy call‑sites may pass a configuration mapping containing an ``interval``
        key.  If omitted, a default interval of 5 seconds is used.

    Returns
    -------
    MemoryMonitor
        The started daemon thread (already ``start()``ed).
    """
    interval = 5.0
    if config is not None:
        try:
            interval = float(config.get("memory_monitor_interval", interval))
        except Exception:  # pragma: no cover
            logger.warning("Invalid interval in config – falling back to default.")
    monitor = MemoryMonitor(interval=interval)
    monitor.start()
    logger.debug("Memory monitor started with interval %.2f seconds", interval)
    return monitor
