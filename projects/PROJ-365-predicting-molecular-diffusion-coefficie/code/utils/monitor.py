"""Utility for enforcing runtime and memory limits on pipeline stages.

This module provides:
- ``ResourceLimitExceeded``: exception raised when a limit is breached.
- ``ResourceMonitor``: background thread that tracks elapsed time and
  resident memory usage, records the peak memory observed and raises
  ``ResourceLimitExceeded`` when a configured limit is exceeded.
- ``enforce_limits``: decorator‑style helper that runs a callable under a
  ``ResourceMonitor`` and writes a JSON report ``artifacts/reports/
  runtime_memory.json`` containing ``total_seconds`` and ``peak_memory_mb``.
- ``run_with_limits``: thin wrapper that forwards any ``ResourceLimitExceeded``
  exception after the report has been written.

The implementation builds on the existing API surface (imports from
``utils.config`` and the standard library) and adds ``psutil`` for reliable
memory measurement.  The JSON report format matches the expectations of
tasks T006c and T006e.
"""

from __future__ import annotations

import json
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any, Callable

import psutil

from utils.config import get_project_root

__all__ = [
    "ResourceLimitExceeded",
    "ResourceMonitor",
    "enforce_limits",
    "run_with_limits",
]


class ResourceLimitExceeded(Exception):
    """Exception raised when a time or memory limit is exceeded."""


class ResourceMonitor:
    """Background monitor that tracks elapsed time and peak memory usage.

    Parameters
    ----------
    time_limit_seconds : int, optional
        Maximum allowed runtime in seconds (default: 6 hours).
    memory_limit_mb : int, optional
        Maximum allowed resident memory in megabytes (default: 7 GB).
    """

    def __init__(self, time_limit_seconds: int = 21600, memory_limit_mb: int = 7 * 1024):
        self.time_limit_seconds = time_limit_seconds
        self.memory_limit_mb = memory_limit_mb
        self.start_time: float | None = None
        self.peak_memory_mb: float = 0.0
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._exception: ResourceLimitExceeded | None = None

    # ------------------------------------------------------------------
    # Internal monitoring loop
    # ------------------------------------------------------------------
    def _monitor(self) -> None:
        """Continuously poll process memory and elapsed time."""
        proc = psutil.Process(os.getpid())
        while not self._stop_event.is_set():
            now = time.time()
            elapsed = now - (self.start_time or now)

            # Time limit enforcement
            if elapsed > self.time_limit_seconds:
                self._exception = ResourceLimitExceeded(
                    f"Time limit of {self.time_limit_seconds}s exceeded (elapsed {elapsed:.2f}s)."
                )
                break

            # Memory usage (RSS) in MB
            mem_mb = proc.memory_info().rss / (1024 * 1024)

            # Record peak memory
            if mem_mb > self.peak_memory_mb:
                self.peak_memory_mb = mem_mb

            # Memory limit enforcement
            if mem_mb > self.memory_limit_mb:
                self._exception = ResourceLimitExceeded(
                    f"Memory limit of {self.memory_limit_mb} MiB exceeded (observed {mem_mb:.2f} MiB)."
                )
                break

            # Small sleep to avoid busy‑waiting
            time.sleep(0.1)

    # ------------------------------------------------------------------
    # Public control methods
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the monitoring thread and record the start time."""
        self.start_time = time.time()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the monitor to stop and join the thread.

        If a limit violation was detected, re‑raise the stored exception.
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join()

        if self._exception is not None:
            raise self._exception

    # ------------------------------------------------------------------
    # Helper for report generation
    # ------------------------------------------------------------------
    def elapsed_seconds(self) -> float:
        """Return the elapsed wall‑clock time in seconds."""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time


def _write_runtime_report(monitor: ResourceMonitor) -> None:
    """Write ``runtime_memory.json`` containing total runtime and peak memory.

    The report is placed under ``artifacts/reports/`` relative to the project
    root.  The directory hierarchy is created if it does not already exist.
    """
    report_path = (
        get_project_root()
        / "artifacts"
        / "reports"
        / "runtime_memory.json"
    )
    os.makedirs(report_path.parent, exist_ok=True)

    report = {
        "total_seconds": round(monitor.elapsed_seconds(), 2),
        "peak_memory_mb": round(monitor.peak_memory_mb, 2),
    }

    with open(report_path, "w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2)


def enforce_limits(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Execute *func* under resource limits and produce a runtime report.

    Parameters
    ----------
    func : Callable
        The target function to run.
    *args, **kwargs :
        Arguments forwarded to *func*.

    Returns
    -------
    Any
        The return value of *func*.

    Raises
    ------
    ResourceLimitExceeded
        If the execution exceeds the configured time or memory limits.
    """
    monitor = ResourceMonitor()
    monitor.start()
    try:
        result = func(*args, **kwargs)
    except Exception:
        # Ensure the monitor is stopped before propagating the exception
        try:
            monitor.stop()
        finally:
            # Write whatever information we have before re‑raising
            _write_runtime_report(monitor)
        raise
    else:
        # Normal completion – stop the monitor and write the report
        monitor.stop()
        _write_runtime_report(monitor)
        return result


def run_with_limits(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Convenient wrapper that runs *func* with ``enforce_limits``."""
    return enforce_limits(func, *args, **kwargs)