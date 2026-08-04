"""
Custom exception classes for the plant defense prediction pipeline.
"""
import sys
from typing import Optional, Dict, Any


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class E_DATASET(PipelineError):
    """Exception raised when dataset issues occur (not found, invalid, download failed)."""
    pass


class E_PAIRING(PipelineError):
    """Exception raised when sample pairing rate is below threshold."""
    pass


class E_TIMEOUT(PipelineError):
    """Exception raised when execution exceeds time limits."""
    pass


class E_POWER(PipelineError):
    """Exception raised when power analysis fails (insufficient sample size)."""
    pass


class E_SAMPLESIZE(PipelineError):
    """Exception raised when sample size is insufficient for analysis."""
    pass


def raise_dataset_error(message: str) -> None:
    """Raise E_DATASET exception with the given message."""
    raise E_DATASET(message)


def raise_pairing_error(message: str) -> None:
    """Raise E_PAIRING exception with the given message."""
    raise E_PAIRING(message)


def raise_timeout_error(message: str) -> None:
    """Raise E_TIMEOUT exception with the given message."""
    raise E_TIMEOUT(message)


def raise_power_error(message: str) -> None:
    """Raise E_POWER exception with the given message."""
    raise E_POWER(message)


def raise_samplesize_error(message: str) -> None:
    """Raise E_SAMPLESIZE exception with the given message."""
    raise E_SAMPLESIZE(message)