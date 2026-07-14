"""
Memory Monitor Module
---------------------
Provides a very lightweight memory‑usage monitor that can be instantiated
without any arguments. The monitor runs a background thread that periodically
checks the process RSS and logs a warning if a user‑defined limit is exceeded.
The API is deliberately tolerant – it accepts arbitrary ``*args``/``**kwargs``
so that callers with differing signatures remain compatible.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

__all__ = ["MemoryMonitor", "setup_memory_monitoring"]

class MemoryMonitor:
    """
    Simple memory‑usage watchdog.

    Parameters
    ----------
    limit_mb: int | None
        Upper bound in megabytes. If ``None`` the monitor is effectively disabled.
    interval: float
        Seconds between successive checks.
    """
    def __init__(self, limit_mb: Optional[int] = None, interval: float = 5.0):
        self.limit_mb = limit_mb
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._monitor_loop, daemon=True, name="MemoryMonitor"
        )
        self._logger = logging.getLogger(self.__class__.__name__)

    def start(self) -> None:
        """Start the background monitoring thread."""
        self._logger.debug("Starting memory monitor (limit=%s MB)", self.limit_mb)
        self._thread.start()

    def stop(self) -> None:
        """Signal the monitor to stop and wait for the thread to finish."""
        self._logger.debug("Stopping memory monitor")
        self._stop_event.set()
        self._thread.join()

    def _monitor_loop(self) -> None:
        """Periodically check RSS and log a warning if the limit is crossed."""
        import psutil  # Imported lazily to avoid a hard dependency during import.

        while not self._stop_event.is_set():
            if self.limit_mb is not None:
                rss_mb = psutil.Process().memory_info().rss / (1024 * 1024)
                if rss_mb > self.limit_mb:
                    self._logger.warning(
                        "Memory usage exceeded limit: %.2f MB > %d MB",
                        rss_mb,
                        self.limit_mb,
                    )
            time.sleep(self.interval)

def setup_memory_monitoring(*args, **kwargs) -> MemoryMonitor:
    """
    Factory function that creates a :class:`MemoryMonitor` instance.

    The function accepts arbitrary positional and keyword arguments for
    compatibility with existing call sites. Recognised arguments are:

    - ``limit_mb`` (int): memory limit in megabytes.
    - ``interval`` (float): polling interval in seconds.

    Unrecognised arguments are ignored.
    """
    limit_mb = kwargs.get("limit_mb")
    interval = kwargs.get("interval", 5.0)

    monitor = MemoryMonitor(limit_mb=limit_mb, interval=interval)
    monitor.start()
    return monitor
