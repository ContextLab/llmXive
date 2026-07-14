"""
memory_monitor.py
-----------------
Provides a lightweight background thread that periodically checks the
process's memory usage against a configurable limit.  The public helper
``setup_memory_monitoring`` accepts either a full configuration object (as
defined in ``config.py``) or no arguments at all, making it compatible with
legacy calls.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

import psutil

from config import (
    get_memory_limit_mb,
    get_max_runtime_seconds,
    get_all_config,
)

logger = logging.getLogger(__name__)

class MemoryMonitor(threading.Thread):
    """
    Background thread that monitors memory consumption.  It runs as a daemon
    so it does not block interpreter shutdown.
    """
    def __init__(self, limit_mb: int, check_interval: float = 1.0) -> None:
        super().__init__(daemon=True)
        self.limit_mb = limit_mb
        self.check_interval = check_interval
        self._stop_event = threading.Event()

    def run(self) -> None:
        logger.info("Memory monitor started (limit %d MB)", self.limit_mb)
        while not self._stop_event.is_set():
            mem = psutil.Process().memory_info().rss / (1024 * 1024)
            if mem > self.limit_mb:
                logger.warning(
                    "Memory usage %.2f MB exceeds limit of %d MB",
                    mem,
                    self.limit_mb,
                )
            time.sleep(self.check_interval)

    def stop(self) -> None:
        self._stop_event.set()

def _resolve_config(*args, **kwargs) -> dict[str, Any]:
    """
    Resolve a configuration mapping from the flexible calling conventions.
    """
    if args:
        # Assume first positional argument is a config dict‑like object
        return dict(args[0])
    if kwargs:
        return dict(kwargs)
    # Fallback to the global config
    return get_all_config()

def setup_memory_monitoring(*args, **kwargs) -> MemoryMonitor:
    """
    Starts the memory monitor.  Accepts an optional configuration object
    (positional or keyword) or no arguments.
    """
    cfg = _resolve_config(*args, **kwargs)
    limit_mb = cfg.get("memory_limit_mb", get_memory_limit_mb())
    monitor = MemoryMonitor(limit_mb=limit_mb)
    monitor.start()
    return monitor
