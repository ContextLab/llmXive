"""
Resource monitoring utilities.

This module provides a ResourceMonitor class that tracks peak RAM usage
(VmRSS) and wall‑clock time for a script execution. It also defines a
`check_resource_limits` helper that enforces project‑wide limits:
  * RAM usage must not exceed 7 GB.
  * Wall‑clock time must not exceed 360 minutes (21 600 seconds).

The monitor raises a ``ValueError`` with a clear message when a limit is
breached. The implementation is deliberately lightweight and avoids any
heavy external dependencies beyond ``psutil``.
"""

from __future__ import annotations

import time
from typing import Optional

import psutil

# ----------------------------------------------------------------------
# Configuration constants (mirrored in the contract test)
# ----------------------------------------------------------------------
RAM_LIMIT_GB: float = 7.0
WALL_CLOCK_LIMIT_MIN: int = 360
WALL_CLOCK_LIMIT_SEC: int = WALL_CLOCK_LIMIT_MIN * 60


def check_resource_limits(peak_ram_gb: float, wall_clock_sec: float) -> None:
    """
    Validate RAM and wall‑clock limits.

    Parameters
    ----------
    peak_ram_gb: float
        Peak RAM usage observed during the run, expressed in gigabytes.
    wall_clock_sec: float
        Total elapsed wall‑clock time in seconds.

    Raises
    ------
    ValueError
        If either limit is exceeded. The error message contains the
        offending limit(s) so that contract tests can assert on the text.
    """
    messages = []

    if peak_ram_gb > RAM_LIMIT_GB:
        messages.append(
            f"RAM limit exceeded: {peak_ram_gb:.2f} GB > {RAM_LIMIT_GB} GB"
        )

    if wall_clock_sec > WALL_CLOCK_LIMIT_SEC:
        minutes = wall_clock_sec / 60
        messages.append(
            f"Wall-clock time limit exceeded: {minutes:.2f} minutes > {WALL_CLOCK_LIMIT_MIN} minutes"
        )

    if messages:
        # Join messages with a semicolon for readability.
        raise ValueError("; ".join(messages))


class ResourceMonitor:
    """
    Context‑style monitor for peak RAM usage and elapsed time.

    Typical usage:
        monitor = ResourceMonitor()
        monitor.start()
        # ... code whose resources you want to track ...
        monitor.stop()   # raises ValueError if limits are breached
    """

    def __init__(self) -> None:
        self._start_time: Optional[float] = None
        self._peak_ram_gb: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Mark the beginning of the monitored interval."""
        self._start_time = time.time()
        # Record an initial RAM measurement.
        self._record_peak_ram()

    def stop(self) -> None:
        """
        Finalise monitoring, record the final RAM measurement and enforce limits.

        Raises
        ------
        ValueError
            Propagated from :func:`check_resource_limits` if a limit is exceeded.
        RuntimeError
            If ``start`` has not been called before ``stop``.
        """
        if self._start_time is None:
            raise RuntimeError("ResourceMonitor.stop() called before start().")

        # Record the final RAM measurement (may be higher than the first one).
        self._record_peak_ram()

        elapsed_sec = time.time() - self._start_time
        # Enforce the configured limits.
        check_resource_limits(self._peak_ram_gb, elapsed_sec)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _record_peak_ram(self) -> None:
        """
        Update the stored peak RAM usage.

        The measurement is taken from the current process's RSS (resident set size)
        using ``psutil`` and converted to gigabytes.
        """
        process = psutil.Process()
        rss_bytes = process.memory_info().rss
        rss_gb = rss_bytes / (1024 ** 3)
        if rss_gb > self._peak_ram_gb:
            self._peak_ram_gb = rss_gb

    # Expose current measurements for external inspection (used by tests).
    @property
    def peak_ram_gb(self) -> float:
        """Current recorded peak RAM usage in gigabytes."""
        return self._peak_ram_gb

    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Elapsed wall‑clock time in seconds, or ``None`` if not started."""
        if self._start_time is None:
            return None
        return time.time() - self._start_time