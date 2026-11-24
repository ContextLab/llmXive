"""
Exception hierarchy for the Euler Totient residue-distribution pipeline.
"""

from __future__ import annotations
from typing import Optional

class TotientError(Exception):
    """Base class for errors raised by totient-related computations."""
    def __init__(self, message: str = "An error occurred in totient computation.") -> None:
        super().__init__(message)

class MemoryLimitExceeded(TotientError):
    """Raised by MemoryGuard when the process exceeds the configured memory limit."""
    def __init__(self, limit_mb: float, usage_mb: float) -> None:
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
        msg = f"Invalid prime modulus {prime}."
        super().__init__(msg)
        self.prime = prime

class BenchmarkFailure(Exception):
    """Raised when the benchmark context manager fails or exceeds a limit."""
    def __init__(self, *, elapsed_time: float, limit: float, path: Optional[str] = None) -> None:
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
    """Signals that a required external resource is missing or invalid."""
    def __init__(self, message: str = "Required research artefact is missing or invalid.") -> None:
        super().__init__(message)
