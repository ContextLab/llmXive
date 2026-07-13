from __future__ import annotations
import logging
import threading
import time
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

class MemoryMonitor(threading.Thread):
    """
    Simple background thread that periodically checks the process memory usage
    and logs a warning if the usage exceeds ``memory_limit_mb``.
    """
    def __init__(self, memory_limit_mb: int = 7000, interval: float = 1.0):
        super().__init__(daemon=True)
        self.memory_limit_mb = memory_limit_mb
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self) -> None:  # pragma: no cover – exercised indirectly
        while not self._stop_event.is_set():
            mem = psutil.Process().memory_info().rss / (1024 * 1024)
            if mem > self.memory_limit_mb:
                logger.warning(
                    f"Memory usage {mem:.1f} MiB exceeds limit of {self.memory_limit_mb} MiB"
                )
            time.sleep(self.interval)

    def stop(self) -> None:
        self._stop_event.set()

def setup_memory_monitoring(*args, **kwargs) -> MemoryMonitor:
    """
    Initialise and start a :class:`MemoryMonitor`.

    Acceptable signatures (all resolve to the same behaviour):
    * ``setup_memory_monitoring()`` – defaults.
    * ``setup_memory_monitoring(memory_limit_mb, interval)`` – positional.
    * ``setup_memory_monitoring(memory_limit_mb=…, interval=…)`` – keyword.
    * ``setup_memory_monitoring(memory_limit_mb=…, interval=…)`` – explicit.

    Returns the started ``MemoryMonitor`` instance.
    """
    # Positional handling
    if args:
        if len(args) >= 1:
            memory_limit_mb = args[0]
        else:
            memory_limit_mb = 7000
        if len(args) >= 2:
            interval = args[1]
        else:
            interval = 1.0
    else:
        memory_limit_mb = kwargs.get("memory_limit_mb", 7000)
        interval = kwargs.get("interval", 1.0)

    monitor = MemoryMonitor(int(memory_limit_mb), float(interval))
    monitor.start()
    logger.debug(
        f"Memory monitor started with limit={memory_limit_mb} MiB, interval={interval}s"
    )
    return monitor