"""
utils.monitor
----------------

This module provides a simple resource monitoring utility that enforces
runtime and memory usage limits for long‑running pipelines.  It also
records the total runtime and peak memory usage to a JSON report at
``artifacts/reports/runtime_memory.json`` as required by the project
specifications.

The public API consists of:

* ``ResourceLimitExceeded`` – exception raised when a limit is exceeded.
* ``ResourceMonitor`` – class that tracks time, memory and writes the JSON
  report.
* ``enforce_limits`` – decorator that runs a function under the monitor.
* ``run_with_limits`` – helper that runs an arbitrary callable under the
  monitor (used by scripts that prefer a functional style).

The implementation relies on ``psutil`` (already declared in
``requirements.txt``) for portable memory measurements and on the
``utils.config.get_project_root`` helper for locating the project root.
"""

from __future__ import annotations

import json
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

import psutil

from utils.config import get_project_root

# ---------------------------------------------------------------------------
# Public exception
# ---------------------------------------------------------------------------
class ResourceLimitExceeded(RuntimeError):
    """Raised when the runtime or memory usage exceeds the configured limits."""
    pass


# ---------------------------------------------------------------------------
# Core monitor implementation
# ---------------------------------------------------------------------------
class ResourceMonitor:
    """
    Tracks execution time and memory usage for a block of code.

    Parameters
    ----------
    time_limit_seconds : int, optional
        Maximum allowed wall‑clock time in seconds.  Default is 6 hours
        (21600 s) as required by the specification.
    memory_limit_mb : int, optional
        Maximum allowed resident set size (RSS) in megabytes.  Default is
        7 GB (7 * 1024 MB).
    """

    def __init__(
        self,
        time_limit_seconds: int = 21600,
        memory_limit_mb: int = 7 * 1024,
    ) -> None:
        self.time_limit = time_limit_seconds
        self.memory_limit = memory_limit_mb
        self._start_time: Optional[float] = None
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._process = psutil.Process(os.getpid())
        self.peak_memory_mb: float = 0.0
        self._limit_exceeded: Optional[ResourceLimitExceeded] = None
        self.total_seconds: Optional[float] = None

    # -------------------------------------------------------------------
    # Lifecycle helpers
    # -------------------------------------------------------------------
    def start(self) -> None:
        """Begin timing and launch the background monitor thread."""
        self._start_time = time.time()
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()

    def stop(self) -> None:
        """Stop the monitor thread and record the total elapsed time."""
        self._stop_event.set()
        if self._monitor_thread is not None:
            self._monitor_thread.join()
        if self._start_time is not None:
            self.total_seconds = time.time() - self._start_time

    # -------------------------------------------------------------------
    # Monitoring loop
    # -------------------------------------------------------------------
    def _monitor(self) -> None:
        """
        Periodically poll the process memory usage and elapsed time.
        If a limit is crossed, store the exception for later raising.
        """
        while not self._stop_event.is_set():
            now = time.time()
            elapsed = now - (self._start_time or now)

            # --- Time limit check -------------------------------------------------
            if self.time_limit and elapsed > self.time_limit:
                self._limit_exceeded = ResourceLimitExceeded(
                    f"Time limit exceeded: {elapsed:.2f}s > {self.time_limit}s"
                )
                break

            # --- Memory usage check -----------------------------------------------
            try:
                mem_rss = self._process.memory_info().rss  # bytes
            except psutil.NoSuchProcess:
                # Process terminated unexpectedly; stop monitoring.
                break
            mem_mb = mem_rss / (1024 * 1024)
            if mem_mb > self.peak_memory_mb:
                self.peak_memory_mb = mem_mb

            if self.memory_limit and mem_mb > self.memory_limit:
                self._limit_exceeded = ResourceLimitExceeded(
                    f"Memory limit exceeded: {mem_mb:.2f} MB > {self.memory_limit} MB"
                )
                break

            time.sleep(0.1)  # poll interval – low enough for responsiveness

    # -------------------------------------------------------------------
    # Result handling
    # -------------------------------------------------------------------
    @property
    def limit_exceeded(self) -> Optional[ResourceLimitExceeded]:
        """Return the stored ``ResourceLimitExceeded`` if a limit was hit."""
        return self._limit_exceeded

    def write_report(self) -> None:
        """
        Persist a JSON report containing ``total_seconds`` and
        ``peak_memory_mb`` to ``artifacts/reports/runtime_memory.json``.
        The directory hierarchy is created on demand.
        """
        report = {
            "total_seconds": round(self.total_seconds or 0.0, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
        }
        report_path = (
            get_project_root() / "artifacts" / "reports" / "runtime_memory.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)


# ---------------------------------------------------------------------------
# Helper decorator – convenient for scripts that define a ``main`` function
# ---------------------------------------------------------------------------
def enforce_limits(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that runs ``func`` under a :class:`ResourceMonitor`.  After the
    wrapped call finishes, the monitor writes the JSON report.  If a limit
    was exceeded, the stored ``ResourceLimitExceeded`` is raised.
    """

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        monitor = ResourceMonitor()
        monitor.start()
        try:
            result = func(*args, **kwargs)
        finally:
            monitor.stop()
            monitor.write_report()
            # Propagate any limit violation after cleanup.
            if monitor.limit_exceeded:
                raise monitor.limit_exceeded
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Functional style entry point – useful for one‑off calls
# ---------------------------------------------------------------------------
def run_with_limits(target: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Execute ``target`` with the same monitoring guarantees as
    ``enforce_limits`` but without using a decorator.

    Parameters
    ----------
    target : callable
        The function to execute under resource limits.
    *args, **kwargs :
        Arguments passed straight through to ``target``.

    Returns
    -------
    Any
        Whatever ``target`` returns (unless a limit is exceeded).

    Raises
    ------
    ResourceLimitExceeded
        If either the time or memory limit is crossed.
    """
    monitor = ResourceMonitor()
    monitor.start()
    try:
        result = target(*args, **kwargs)
    finally:
        monitor.stop()
        monitor.write_report()
        if monitor.limit_exceeded:
            raise monitor.limit_exceeded
    return result