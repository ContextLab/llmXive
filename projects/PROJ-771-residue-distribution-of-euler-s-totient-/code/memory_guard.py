"""
MemoryGuard module.

Provides a guard that monitors the current process memory usage
(``psutil.Process().memory_info().rss``) and raises
:class:`exceptions.MemoryLimitExceeded` when the usage exceeds
90 % of the configured ``memory_limit_mb``.

The guard is polled every ``check_interval`` iterations (default
10 000, matching the sieve specification): ``check(iteration)``
only inspects memory when ``iteration`` is ``None`` or a multiple
of ``check_interval``.
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
        compares the resident set size (RSS) against 90 % of this
        limit and raises :class:`MemoryLimitExceeded` when the
        threshold is crossed.
    limit_percent : float, optional
        Percentage of total system memory that may be used
        (default 90.0).  Used only when ``limit_mb`` is ``None``.
    check_interval : int, optional
        How often (in iterations) the guard polls memory usage.
        Defaults to 10 000.
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
        self._process: psutil.Process = psutil.Process()

    def _usage_mb(self) -> float:
        """Return current RSS usage in megabytes."""
        rss_bytes = self._process.memory_info().rss
        return rss_bytes / (1024 * 1024)

    def _usage_percent(self) -> float:
        """Return overall system memory usage as a percentage."""
        vm = psutil.virtual_memory()
        return vm.percent

    def _raise_limit_exceeded(
        self,
        limit_mb: Optional[float],
        usage_mb: Optional[float],
    ) -> None:
        """Raise :class:`MemoryLimitExceeded` with a clear message.

        The exception constructor signature varies across
        revisions of ``code/exceptions.py`` (it may accept a
        single message string, or ``(limit_mb, usage_mb)``).
        This helper tries the known signatures in order and
        always raises ``MemoryLimitExceeded` carrying a
        human‑readable description of the breach.
        """
        message = (
            "Memory limit exceeded: usage {:.2f} MB is above "
            "90% of the configured limit {} MB".format(
                -1.0 if usage_mb is None else usage_mb,
                "unknown" if limit_mb is None else limit_mb,
            )
        )
        for args in (
            (message,),
            (limit_mb, usage_mb),
            (limit_mb, usage_mb, message),
        ):
            try:
                raise MemoryLimitExceeded(*args)
            except TypeError:
                continue
        # Last resort: bare construction.
        raise MemoryLimitExceeded(message)

    def check(self, iteration: Optional[int] = None) -> bool:
        """
        Perform a memory‑usage check.

        Parameters
        ----------
        iteration : int, optional
            Current iteration count of the surrounding algorithm
            (e.g. the sieve loop index).  If omitted, the check is
            performed unconditionally.

        Returns
        -------
        bool
            ``True`` if memory usage is within limits.

        Raises
        ------
        MemoryLimitExceeded
            If usage exceeds 90 % of ``limit_mb`` (or
            ``limit_percent`` of system memory when no absolute
            limit is configured).
        """
        if iteration is not None and iteration % self.check_interval != 0:
            return True  # No check needed this iteration.

        if self.limit_mb is not None:
            threshold_mb = 0.9 * self.limit_mb
            usage_mb = self._usage_mb()
            if usage_mb > threshold_mb:
                self._raise_limit_exceeded(self.limit_mb, usage_mb)
        else:
            usage_percent = self._usage_percent()
            if usage_percent > self.limit_percent:
                self._raise_limit_exceeded(None, None)

        return True
