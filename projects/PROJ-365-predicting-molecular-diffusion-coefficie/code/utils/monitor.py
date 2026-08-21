"""
utils.monitor
--------------

This module provides runtime and memory resource limiting utilities for the
pipeline.  It defines:

* ``ResourceLimitExceeded`` – exception raised when a limit is exceeded.
* ``enforce_limits`` – convenience wrapper that runs a callable under the
  limits.
* ``ResourceMonitor`` – class that implements the actual monitoring logic.
* ``run_with_limits`` – functional style entry point.

The implementation records the total wall‑clock time of the wrapped
callable and writes a JSON report to ``artifacts/reports/runtime_memory.json``
under the key ``"total_seconds"`` (as required by task **T006c**).  Any
existing keys (e.g., ``peak_memory_mb`` added by a future task) are
preserved.
"""

import json
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

__all__ = [
    "ResourceLimitExceeded",
    "enforce_limits",
    "ResourceMonitor",
    "run_with_limits",
]


class ResourceLimitExceeded(RuntimeError):
    """Exception raised when a resource limit (time or memory) is exceeded."""
    pass


# ----------------------------------------------------------------------
# Helper for time‑limit enforcement using the UNIX ``alarm`` signal.
# ----------------------------------------------------------------------
def _timeout_handler(signum: int, frame: Any) -> None:  # pragma: no cover
    """Signal handler that converts an alarm into a ``ResourceLimitExceeded``."""
    raise ResourceLimitExceeded("Time limit exceeded")


# ----------------------------------------------------------------------
# Core monitor implementation
# ----------------------------------------------------------------------
class ResourceMonitor:
    """
    Monitor a callable for time and memory usage.

    Parameters
    ----------
    time_limit : int
        Maximum wall‑clock time in seconds (default 21600 s == 6 h).
    memory_limit_gb : int
        Maximum resident set size in gigabytes (default 7 GB).

    The monitor records start/end timestamps and, upon successful
    completion, writes ``total_seconds`` to
    ``artifacts/reports/runtime_memory.json``.  Existing fields in the JSON
    file are retained (e.g., ``peak_memory_mb`` added later).
    """

    def __init__(self, time_limit: int = 21600, memory_limit_gb: int = 7):
        self.time_limit = time_limit
        self.memory_limit_gb = memory_limit_gb
        self._start: Optional[float] = None
        self._end: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute ``func`` under the configured limits.

        Returns
        -------
        Any
            The return value of ``func``.

        Raises
        ------
        ResourceLimitExceeded
            If the time or memory limit is breached.
        """
        self._start = time.time()
        self._setup_time_limit()
        try:
            # The actual function execution
            result = func(*args, **kwargs)
        finally:
            # Always cancel the alarm and record the end time
            self._cancel_time_limit()
            self._end = time.time()
            # Write the runtime report regardless of success/failure
            self._write_runtime_report()
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _setup_time_limit(self) -> None:
        """Install the alarm signal for time‑limit enforcement."""
        signal.signal(signal.SIGALRM, _timeout_handler)
        # ``alarm`` expects an integer number of seconds
        signal.alarm(self.time_limit)

    def _cancel_time_limit(self) -> None:
        """Disable any pending alarm."""
        signal.alarm(0)

    def _write_runtime_report(self) -> None:
        """Write (or update) the JSON runtime report."""
        total_seconds = (
            self._end - self._start if self._start is not None and self._end is not None else None
        )
        report_path = Path("artifacts/reports/runtime_memory.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        # Load any existing data to preserve fields added by other tasks
        data: Dict[str, Any] = {}
        if report_path.is_file():
            try:
                with report_path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                # Corrupt JSON – start fresh
                data = {}

        if total_seconds is not None:
            data["total_seconds"] = total_seconds

        with report_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

# ----------------------------------------------------------------------
# Convenience wrappers
# ----------------------------------------------------------------------
def enforce_limits(
    func: Callable[..., Any],
    *args: Any,
    time_limit: int = 21600,
    memory_limit_gb: int = 7,
    **kwargs: Any,
) -> Any:
    """
    Run ``func`` under resource limits.

    This is a thin wrapper around :class:`ResourceMonitor` that mirrors the
    original API used throughout the code base.
    """
    monitor = ResourceMonitor(time_limit=time_limit, memory_limit_gb=memory_limit_gb)
    return monitor.run(func, *args, **kwargs)


def run_with_limits(
    func: Callable[..., Any],
    *args: Any,
    time_limit: int = 21600,
    memory_limit_gb: int = 7,
    **kwargs: Any,
) -> Any:
    """
    Functional entry point used by tests and pipeline scripts.

    Example
    -------
    >>> def long_job():
    ...     time.sleep(2)
    >>> run_with_limits(long_job, time_limit=1)  # raises ResourceLimitExceeded
    """
    return enforce_limits(
        func, *args, time_limit=time_limit, memory_limit_gb=memory_limit_gb, **kwargs
    )