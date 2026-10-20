"""
Exception hierarchy for the Euler Totient residue‑distribution pipeline.

The module defines a set of domain‑specific exceptions used throughout the
code‑base.  All exceptions inherit from :class:`Exception` and provide a
clear, human‑readable error message.  The messages are deliberately short
because they are logged or displayed directly to the user.
"""

from __future__ import annotations
from typing import Optional

class TotientError(Exception):
    """Base class for errors raised by totient‑related computations."""
    def __init__(self, message: str = "An error occurred in totient computation.") -> None:
        super().__init__(message)


class MemoryLimitExceeded(TotientError):
    """
    Raised by :class:`MemoryGuard` when the process exceeds the configured
    memory limit.

    Parameters
    ----------
    limit_mb : int
        Configured memory limit in megabytes.
    usage_mb : float
        Current memory usage in megabytes at the moment the limit was
        exceeded.
    """
    def __init__(self, limit_mb: int, usage_mb: float) -> None:
        msg = (
            f"Memory usage {usage_mb:.2f} MiB exceeded the limit of "
            f"{limit_mb} MiB (90 % threshold)."
        )
        super().__init__(msg)
        self.limit_mb = limit_mb
        self.usage_mb = usage_mb


class InvalidPrimeError(TotientError):
    """Raised when a user supplies a prime that is not supported."""
    def __init__(self, prime: int) -> None:
        super().__init__(f"Prime {prime} is not among the supported set { {3,5,7,11} }.")


class BenchmarkFailure(Exception):
    """Raised when the benchmark context manager cannot write its JSON report."""
    def __init__(self, path: str, reason: str) -> None:
        super().__init__(f"Failed to write benchmark report to {path}: {reason}")
        self.path = path
        self.reason = reason


class ResearchIncompleteError(Exception):
    """
    Signals that a required external resource (e.g. a constants file or a
    schema) is missing or could not be loaded.  The pipeline aborts with a
    clear error message when this exception is raised.
    """
    def __init__(self, message: str = "Required research artefact is missing or invalid.") -> None:
        super().__init__(message)
