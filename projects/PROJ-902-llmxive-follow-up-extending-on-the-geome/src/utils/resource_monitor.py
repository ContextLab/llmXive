"""
Resource monitoring utilities.

This module provides a context manager and helper functions to record the
peak resident set size (VmRSS) and wall‑clock time of a code block or
function execution.  It also enforces the resource limits required by the
project contracts:

* Maximum RAM usage: 7 GB
* Maximum wall‑clock time: 360 minutes (6 hours)

If a limit is exceeded, a :class:`ResourceLimitExceeded` exception is raised.
"""

import sys
import time
import json
import resource
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = [
    "ResourceLimitExceeded",
    "ResourceMonitor",
    "monitor_function",
    "write_resource_summary",
]


class ResourceLimitExceeded(RuntimeError):
    """Exception raised when a resource limit is exceeded."""

    pass


class ResourceMonitor:
    """
    Context manager that records peak RSS (VmRSS) and wall‑clock time.

    Example
    -------
    >>> from src.utils.resource_monitor import ResourceMonitor
    >>> with ResourceMonitor() as rm:
    ...     # code to monitor
    ...     do_something()
    >>> print(rm.peak_ram_gb, rm.elapsed_seconds)
    """

    # Default limits as dictated by the specification
    DEFAULT_MAX_RAM_GB = 7.0
    DEFAULT_MAX_WALL_MINUTES = 360.0

    def __init__(
        self,
        max_ram_gb: float = DEFAULT_MAX_RAM_GB,
        max_wall_minutes: float = DEFAULT_MAX_WALL_MINUTES,
    ) -> None:
        self.max_ram_gb = max_ram_gb
        self.max_wall_minutes = max_wall_minutes

        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self.elapsed_seconds: Optional[float] = None
        self.peak_rss_bytes: Optional[int] = None
        self.peak_ram_gb: Optional[float] = None

    # -----------------------------------------------------------------
    # Context‑manager protocol
    # -----------------------------------------------------------------
    def __enter__(self) -> "ResourceMonitor":
        self._start_time = time.perf_counter()
        # ``resource.getrusage`` reports cumulative usage; we only need the
        # peak RSS which will be queried on exit.
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._end_time = time.perf_counter()
        self.elapsed_seconds = self._end_time - self._start_time  # type: ignore[arg-type]

        # ``resource.getrusage`` returns ru_maxrss in kilobytes on Linux
        # and in bytes on macOS.  Normalise to bytes.
        usage = resource.getrusage(resource.RUSAGE_SELF)
        if sys.platform.startswith("darwin"):
            # macOS reports bytes directly
            self.peak_rss_bytes = usage.ru_maxrss
        else:
            # Linux reports kilobytes
            self.peak_rss_bytes = usage.ru_maxrss * 1024

        self.peak_ram_gb = self.peak_rss_bytes / (1024 ** 3)

        # Enforce limits – raise if violated
        if self.peak_ram_gb > self.max_ram_gb:
            raise ResourceLimitExceeded(
                f"Peak RAM usage {self.peak_ram_gb:.2f} GB exceeds the "
                f"limit of {self.max_ram_gb:.2f} GB."
            )
        if (self.elapsed_seconds / 60.0) > self.max_wall_minutes:
            raise ResourceLimitExceeded(
                f"Wall‑clock time {self.elapsed_seconds/60.0:.2f} min exceeds "
                f"the limit of {self.max_wall_minutes:.2f} min."
            )
        # Returning False propagates any exception that may have occurred
        # inside the block.
        return False

    # -----------------------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------------------
    @property
    def wall_clock_minutes(self) -> Optional[float]:
        """Wall‑clock time expressed in minutes."""
        if self.elapsed_seconds is None:
            return None
        return self.elapsed_seconds / 60.0

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable dictionary of the recorded metrics."""
        return {
            "peak_ram_gb": round(self.peak_ram_gb, 6) if self.peak_ram_gb is not None else None,
            "wall_clock_seconds": round(self.elapsed_seconds, 6) if self.elapsed_seconds is not None else None,
            "wall_clock_minutes": round(self.wall_clock_minutes, 6) if self.wall_clock_minutes is not None else None,
        }


def monitor_function(func, *args, **kwargs) -> Any:
    """
    Execute ``func`` while monitoring resources.

    Returns whatever ``func`` returns.  After execution the function's
    resource usage can be inspected via the returned ``ResourceMonitor``
    instance attached as ``.monitor`` on the result (if the result is an
    object) or via the ``monitor`` attribute on the wrapper function.

    Example
    -------
    >>> def work(): time.sleep(1)
    >>> result = monitor_function(work)
    >>> # ``result`` is whatever ``work`` returns; the monitor is
    >>> # available as ``monitor_function.monitor``.
    """
    monitor = ResourceMonitor()
    with monitor:
        result = func(*args, **kwargs)
    # Attach the monitor for introspection by callers/tests
    setattr(result, "monitor", monitor) if not isinstance(result, type(None)) else None
    # Also expose via a attribute on the helper for convenience
    monitor_function.monitor = monitor  # type: ignore[attr-defined]
    return result


def write_resource_summary(
    metrics: Dict[str, Any],
    output_path: Path = Path("ci_metrics.json"),
) -> None:
    """
    Write a JSON file containing the supplied ``metrics`` dictionary.

    The default location matches the contract test that expects a
    ``ci_metrics.json`` file at the repository root (or current working
    directory).  The function creates parent directories as needed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, sort_keys=True)