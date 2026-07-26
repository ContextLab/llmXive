"""
Custom exception classes for the plant defense compound prediction pipeline.
Implements specific error codes as per plan.md:
- E-DATASET: Data acquisition failures
- E-PAIRING: Sample pairing failures
- E-TIMEOUT: Execution time limit exceeded
- E-POWER: Power analysis failures (insufficient sample size)
- E-SAMPLESIZE: General sample size validation failures
"""
import sys
from typing import Optional, Dict, Any


class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.message = message
        
        # Log the error to stderr for immediate visibility
        print(f"[ERROR] {error_code}: {message}", file=sys.stderr)
        if self.details:
            print(f"Details: {self.details}", file=sys.stderr)


class E_DATASET(PipelineError):
    """
    Raised when dataset acquisition fails or no verified plant omics datasets are found.
    Triggers project halt per Phase 0 abort criteria.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "E-DATASET", details)


class E_PAIRING(PipelineError):
    """
    Raised when sample-level pairing rate falls below the required threshold (FR-009: ≥95%).
    Triggers immediate abort as per spec.md edge case handling.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "E-PAIRING", details)


class E_TIMEOUT(PipelineError):
    """
    Raised when execution time exceeds the computational budget (FR-008: ≤4h).
    Used by the runtime timer in main.py and task T008.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "E-TIMEOUT", details)


class E_POWER(PipelineError):
    """
    Raised when power analysis indicates insufficient sample size for statistical validity.
    Required for task T007 and power analysis failures per plan.md.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "E-POWER", details)


class E_SAMPLESIZE(PipelineError):
    """
    Raised for general sample size validation failures (e.g., exploratory model requirements).
    Distinct from E-POWER which is specific to statistical power calculations.
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "E-SAMPLESIZE", details)


# Helper functions to raise errors with consistent formatting
def raise_dataset_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to raise E_DATASET."""
    raise E_DATASET(message, details)


def raise_pairing_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to raise E_PAIRING."""
    raise E_PAIRING(message, details)


def raise_timeout_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to raise E_TIMEOUT."""
    raise E_TIMEOUT(message, details)


def raise_power_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to raise E_POWER."""
    raise E_POWER(message, details)


def raise_samplesize_error(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to raise E_SAMPLESIZE."""
    raise E_SAMPLESIZE(message, details)
