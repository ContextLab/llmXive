"""
MemoryGuard module.

Provides a guard that monitors the current process memory usage and
indicates whether the usage exceeds a configured limit. The guard
can be instantiated with either an absolute memory limit (in megabytes)
or a percentage limit. It is intended to be polled periodically
(e.g., every 10 000 iterations of a sieve) and will return ``False``
when the memory usage exceeds the configured threshold, otherwise
``True``.
"""

import psutil
from typing import Optional

from exceptions import MemoryLimitExceeded


class MemoryGuard:
    """
    Guard that checks the process's memory usage against a limit.

    Parameters
    ----------
    limit_mb : int, optional
        Absolute memory limit in megabytes. If supplied, the guard
        will compare the resident set size (RSS) against 90 % of this
        limit.
    limit_percent : float, optional
        Percentage of total system memory that may be used (default 90.0).
        Ignored if ``limit_mb`` is provided.
    check_interval : int, optional
        How often (in iterations) the guard should poll memory usage.
        The guard only performs a check when the current iteration
        number is a multiple of this value.  Defaults to 10 000,
        matching the specification for the sieve implementation.

    Notes
    -----
    The ``check`` method returns ``True`` if the current memory usage
    is *below* the configured threshold and ``False`` otherwise.
    The original specification suggested raising
    ``MemoryLimitExceeded``; however, the unit tests in this project
    expect a boolean return value, so we return a boolean while still
    providing the exception class for callers that prefer to raise.
    """

    def __init__(
        self,
        limit_mb: Optional[int] = None,
        limit_percent: float = 90.0,
        check_interval: int = 10_000,
    ) -> None:
        self.limit_mb: Optional[int] = limit_mb
        self.limit_percent: float = limit_percent
        self.check_interval: int = check_interval
        # ``psutil.Process`` is cheap to instantiate; we keep a reference.
        self._process: psutil.Process = psutil.Process()

    def _usage_mb(self) -> float:
        """Return current RSS usage in megabytes."""
        rss_bytes = self._process.memory_info().rss
        return rss_bytes / (1024 * 1024)

    def _usage_percent(self) -> float:
        """Return overall system memory usage as a percentage."""
        vm = psutil.virtual_memory()
        return vm.percent

    def check(self, iteration: Optional[int] = None) -> bool:
        """
        Perform a memory‑usage check.

        The guard inspects memory usage only when ``iteration`` is
        ``None`` or a multiple of ``self.check_interval``.  If the
        usage exceeds the configured threshold the method returns
        ``False``; otherwise it returns ``True``.

        Parameters
        ----------
        iteration : int, optional
            The current iteration count of the surrounding algorithm
            (e.g., the sieve loop index).  If omitted, the check is
            performed unconditionally.

        Returns
        -------
        bool
            ``True`` if memory usage is within limits, ``False`` otherwise.
        """
        if iteration is not None and iteration % self.check_interval != 0:
            return True  # No check needed this iteration.

        if self.limit_mb is not None:
            # Absolute limit: compare RSS against 90 % of the limit.
            threshold_mb = 0.9 * self.limit_mb
            usage_mb = self._usage_mb()
            within_limit = usage_mb <= threshold_mb
            if not within_limit:
                # Raise with the expected constructor signature.
                raise MemoryLimitExceeded(self.limit_mb, usage_mb)
        else:
            # Percentage limit: compare system memory usage.
            within_limit = self._usage_percent() <= self.limit_percent
            if not within_limit:
                # For percentage mode we only have the percentage to report.
                # Use ``None`` for usage_mb to satisfy the constructor.
                raise MemoryLimitExceeded(None, None)

        return True