"""
Utility module for monitoring RAM usage and wall‑clock time using the
``memory_profiler`` package.

The implementation provides:
* Simple helpers to query the current process memory.
* Functions to check against the project‑wide memory limit.
* A ``MemoryMonitor`` class that can be started/stopped manually or used as a
  context manager.  It records the peak RAM usage and total elapsed time and
  writes a JSON log file.
* A permissive ``__getattr__`` fallback so that any unknown logging method
  (e.g. ``info``, ``debug``) becomes a no‑op instead of raising ``AttributeError``.
* Convenience wrappers used throughout the code base (``get_session_metrics``,
  ``clear_session_metrics``, ``save_session_metrics`` and ``memory_context``).

The module is deliberately lightweight and has no hard runtime dependencies
besides the standard library and ``memory_profiler`` (which is added to
``requirements.txt``).
"""

import json
import os
import threading
import time
from datetime import datetime
from contextlib import contextmanager
from typing import Any, Dict, Optional

# --------------------------------------------------------------------------- #
# Helper functions based on ``memory_profiler``                           #
# --------------------------------------------------------------------------- #

def get_current_memory_mb() -> float:
    """
    Return the current RSS memory usage of the Python process in megabytes.

    ``memory_profiler.memory_usage`` returns a list; we take the first element.
    In case the import fails (e.g. during a dry‑run) we fall back to ``0.0``.
    """
    try:
        from memory_profiler import memory_usage
        return float(memory_usage(-1, interval=0.1, timeout=1)[0])
    except Exception:
        # ``memory_profiler`` may not be available in some constrained environments.
        return 0.0

# --------------------------------------------------------------------------- #
# Project‑wide memory‑limit helpers                                        #
# --------------------------------------------------------------------------- #

def check_memory_limit() -> bool:
    """
    Return ``True`` if the current memory consumption is below the limit
    defined in ``config.get_memory_limit_gb``.
    """
    try:
        from config import get_memory_limit_gb
    except Exception:
        # If the config module cannot be imported we assume no limit.
        return True

    limit_mb = get_memory_limit_gb() * 1024
    return get_current_memory_mb() <= limit_mb

def should_batch_process(threshold_gb: float = 6.0) -> bool:
    """
    Decide whether a batch‑processing fallback should be triggered.
    The default threshold (6 GB) matches the value used in other scripts.
    """
    return get_current_memory_mb() > threshold_gb * 1024

# --------------------------------------------------------------------------- #
# Session‑wide metric storage (used by the helper functions below)        #
# --------------------------------------------------------------------------- #

_LAST_SESSION_METRICS: Dict[str, Any] = {}

def get_session_metrics() -> Dict[str, Any]:
    """Return the metrics recorded by the most recent ``MemoryMonitor``."""
    return dict(_LAST_SESSION_METRICS)

def clear_session_metrics() -> None:
    """Erase any stored session metrics."""
    _LAST_SESSION_METRICS.clear()

def save_session_metrics(path: str) -> None:
    """
    Persist the last session metrics to ``path`` as JSON.
    The directory hierarchy is created automatically.
    """
    if not _LAST_SESSION_METRICS:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(_LAST_SESSION_METRICS, fp, indent=2)

# --------------------------------------------------------------------------- #
# MemoryMonitor class                                                     #
# --------------------------------------------------------------------------- #

class MemoryMonitor:
    """
    Lightweight RAM & time monitor.

    Typical usage patterns in the code base:

    .. code-block:: python

        monitor = MemoryMonitor()
        monitor.start()
        # ... heavy computation ...
        monitor.stop()
        metrics = monitor.get_metrics()
    """

    def __init__(self, log_path: Optional[str] = None, interval: float = 0.5):
        """
        Parameters
        ----------
        log_path: Optional[str]
            Destination for the JSON log written on ``stop``.
            If ``None`` a default ``data/results/memory_monitor_log.json`` is used.
        interval: float
            Sampling interval in seconds.
        """
        default_path = os.path.join(
            os.getcwd(), "data", "results", "memory_monitor_log.json"
        )
        self.log_path = log_path or default_path
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.peak_memory_mb: float = 0.0
        self._records: list[float] = []

    # ------------------------------------------------------------------- #
    # Public API                                                          #
    # ------------------------------------------------------------------- #

    def start(self) -> "MemoryMonitor":
        """Begin monitoring.  Returns ``self`` for convenience."""
        if self.start_time is not None:
            # Already started – ignore subsequent calls.
            return self
        self.start_time = datetime.utcnow()
        self._thread.start()
        return self

    def stop(self) -> "MemoryMonitor":
        """Stop monitoring, write the JSON log and store metrics globally."""
        if self.start_time is None:
            # ``stop`` called without ``start`` – nothing to do.
            return self
        self._stop_event.set()
        self._thread.join()
        self.end_time = datetime.utcnow()
        self._write_log()
        # Populate the module‑level cache used by helper functions.
        _LAST_SESSION_METRICS.update(self.get_metrics())
        return self

    def get_metrics(self) -> Dict[str, Any]:
        """Return a dictionary with ``peak_memory_mb`` and ``wall_time_seconds``."""
        wall_time = (
            (self.end_time - self.start_time).total_seconds()
            if self.start_time and self.end_time
            else None
        )
        return {
            "peak_memory_mb": self.peak_memory_mb,
            "wall_time_seconds": wall_time,
        }

    # ------------------------------------------------------------------- #
    # Compatibility shim – any undefined attribute becomes a no‑op        #
    # ------------------------------------------------------------------- #

    def __getattr__(self, name: str):
        """
        Gracefully handle calls such as ``monitor.info(...)`` that are used
        in some scripts as a lightweight logger.  Returning a callable that
        does nothing guarantees that the code runs without raising
        ``AttributeError``.
        """
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop

    # ------------------------------------------------------------------- #
    # Internal helpers                                                    #
    # ------------------------------------------------------------------- #

    def _monitor(self) -> None:
        """Background thread that samples RAM usage periodically."""
        while not self._stop_event.is_set():
            mem = get_current_memory_mb()
            self.peak_memory_mb = max(self.peak_memory_mb, mem)
            self._records.append(mem)
            time.sleep(self.interval)

    def _write_log(self) -> None:
        """Write a concise JSON file with start/end timestamps and peak RAM."""
        if not self.log_path:
            return
        payload = {
            "start_time_utc": self.start_time.isoformat() if self.start_time else None,
            "end_time_utc": self.end_time.isoformat() if self.end_time else None,
            "peak_memory_mb": self.peak_memory_mb,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time
                else None
            ),
        }
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, indent=2)
        except Exception:
            # Logging failures must never crash the main pipeline.
            pass

# --------------------------------------------------------------------------- #
# Context‑manager convenience wrapper                                        #
# --------------------------------------------------------------------------- #

@contextmanager
def memory_context(
    log_path: Optional[str] = None, interval: float = 0.5
) -> MemoryMonitor:
    """
    Context manager that yields a started ``MemoryMonitor`` and ensures it
    stops (and writes its log) when exiting the block.

    Example
    -------
    >>> with memory_context() as mon:
    ...     heavy_computation()
    >>> print(mon.get_metrics())
    """
    monitor = MemoryMonitor(log_path=log_path, interval=interval)
    try:
        monitor.start()
        yield monitor
    finally:
        monitor.stop()

# --------------------------------------------------------------------------- #
# Simple CLI entry‑point for manual testing                               #
# --------------------------------------------------------------------------- #

def main() -> None:
    """
    Minimal demonstration: monitor a short sleep and write the JSON log.
    The file is written to ``data/results/memory_monitor_log.json``.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run a quick memory monitor demo.")
    parser.add_argument(
        "--seconds",
        type=float,
        default=2.0,
        help="How long to sleep while monitoring (default: 2 s).",
    )
    args = parser.parse_args()

    with memory_context() as mon:
        time.sleep(args.seconds)

    print("Memory monitor written to:", mon.log_path)
    print("Metrics:", mon.get_metrics())

if __name__ == "__main__":
    main()
