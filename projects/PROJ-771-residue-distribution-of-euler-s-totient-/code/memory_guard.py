"""
MemoryGuard module.

Provides a guard that monitors the current process memory usage and raises
``MemoryLimitExceeded`` when usage exceeds 90 % of a configured limit.
The guard is intended to be polled periodically (e.g., every 10 000
iterations of a sieve) and will raise an exception if the memory usage
threshold is crossed.
"""

import psutil
from typing import Optional

from exceptions import MemoryLimitExceeded


class MemoryGuard:
    """
    Guard that checks the process's resident memory usage against a limit.

    Parameters
    ----------
    limit_mb : int
        The absolute memory limit in megabytes.
    check_interval : int, optional
        How often (in iterations) the guard should poll memory usage.
        Defaults to 10 000, matching the specification for the sieve
        implementation.

    Notes
    -----
    The guard raises :class:`MemoryLimitExceeded` when the resident set
    size (RSS) exceeds 90 % of ``limit_mb``.  The check is performed only
    when the current iteration number is a multiple of ``check_interval``.
    """

    def __init__(self, limit_mb: int, check_interval: int = 10_000) -> None:
        self.limit_mb: int = limit_mb
        self.threshold_mb: float = 0.9 * limit_mb
        self.check_interval: int = check_interval
        # ``psutil.Process`` is cheap to instantiate; we keep a reference.
        self._process: psutil.Process = psutil.Process()

    def _current_rss_mb(self) -> float:
        """Return the current resident memory usage in megabytes."""
        rss_bytes = self._process.memory_info().rss
        return rss_bytes / (1024 * 1024)

    def check(self, iteration: int) -> None:
        """
        Perform a memory‑usage check.

        The guard inspects memory usage only when ``iteration`` is a
        multiple of ``self.check_interval``.  If the usage exceeds the
        90 % threshold, ``MemoryLimitExceeded`` is raised with a helpful
        message.

        Parameters
        ----------
        iteration : int
            The current iteration count of the surrounding algorithm
            (e.g., the sieve loop index).

        Raises
        ------
        MemoryLimitExceeded
            If the current RSS exceeds 90 % of the configured limit.
        """
        if iteration % self.check_interval != 0:
            return  # No check needed this iteration.

        usage_mb = self._current_rss_mb()
        if usage_mb > self.threshold_mb:
            raise MemoryLimitExceeded(
                f"Memory usage {usage_mb:.2f} MiB exceeds 90 % of the "
                f"configured limit ({self.limit_mb} MiB)."
            )

    # Allow the guard to be called like a function for convenience.
    __call__ = check
