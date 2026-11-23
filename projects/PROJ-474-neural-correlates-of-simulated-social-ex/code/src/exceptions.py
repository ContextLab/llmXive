"""
Custom exceptions for the Neural Correlates of Simulated Social Exclusion pipeline.
"""
from typing import Optional


class PipelineError(Exception):
    """Base class for all pipeline-specific errors."""
    pass


class DataUnavailableError(ValueError):
    """Raised when required data files or trial markers cannot be found."""

    def __init__(self, reason: str):
        super().__init__(f"Data unavailable: {reason}")


class InsufficientDataError(ValueError):
    """Raised when data quality or quantity is insufficient for analysis."""
    pass


class InsufficientSubjectsError(ValueError):
    """Raised when the number of retained subjects is below the minimum required (N<10)."""

    def __init__(self, count: int):
        super().__init__(f"Insufficient subjects (N={count}) for valid permutation test.")


class ConfigError(ValueError):
    """Raised when configuration loading or validation fails."""
    pass


class IntegrityError(ValueError):
    """Raised when data integrity checks (e.g., checksums) fail."""
    pass


def raise_data_unavailable(reason: str) -> None:
    """Helper to raise DataUnavailableError."""
    raise DataUnavailableError(reason)


def raise_n_insufficient(count: int) -> None:
    """Helper to raise InsufficientSubjectsError."""
    raise InsufficientSubjectsError(count)
