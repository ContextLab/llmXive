"""
Exception hierarchy for the Euler Totient residue-distribution pipeline.

This module defines a set of domain-specific exceptions used throughout the
code-base. All exceptions inherit from :class:`TotientError` and provide a
clear, human-readable error message that matches the expectations of the
unit tests (see ``tests/unit/test_exceptions.py``).
"""

from __future__ import annotations
from typing import Optional

class TotientError(Exception):
    """Base class for errors raised by totient-related computations."""
    def __init__(self, message: str = "An error occurred in totient computation.") -> None:
        super().__init__(message)


class MemoryLimitExceeded(TotientError):
    """
    Raised by :class:`MemoryGuard` when the process exceeds the configured
    memory limit.

    Parameters
    ----------
    limit_mb : float
        Configured memory limit in megabytes.
    usage_mb : float
        Current memory usage in megabytes at the moment the limit was
        exceeded.
    """
    def __init__(self, limit_mb: float, usage_mb: float) -> None:
        # Standard space used for compatibility and test matching.
        msg = (
            f"Memory limit exceeded: usage {usage_mb:.2f} MiB exceeds "
            f"limit {limit_mb:.2f} MiB."
        )
        super().__init__(msg)
        self.limit_mb = limit_mb
        self.usage_mb = usage_mb


class InvalidPrimeError(TotientError):
    """Raised when a user supplies a prime that is not supported."""
    def __init__(self, prime: int) -> None:
        # The test expects the phrase “Invalid prime modulus <prime>”.
        msg = f"Invalid prime modulus {prime}."
        super().__init__(msg)
        self.prime = prime


class BenchmarkFailure(Exception):
    """
    Raised when the benchmark context manager cannot write its JSON report
    or when the benchmark exceeds a user-supplied time limit.

    The test suite constructs this exception with the keyword arguments
    ``elapsed_time`` and ``limit``; therefore the signature must accept
    those names.
    """
    def __init__(self, *, elapsed_time: float, limit: float, path: Optional[str] = None) -> None:
        # Provide a message that contains “Benchmark failed” and the
        # elapsed time formatted to two decimal places, as required by the tests.
        msg = (
            f"Benchmark failed: elapsed_time {elapsed_time:.2f}s exceeds "
            f"limit {limit:.2f}s."
        )
        if path:
            msg += f" Report path: {path}"
        super().__init__(msg)
        self.elapsed_time = elapsed_time
        self.limit = limit
        self.path = path


class ResearchIncompleteError(Exception):
    """
    Signals that a required external resource (e.g. a constants file or a
    schema) is missing or could not be loaded. The pipeline aborts with a
    clear error message when this exception is raised.
    """
    def __init__(self, message: str = "Required research artefact is missing or invalid.") -> None:
        super().__init__(message)
