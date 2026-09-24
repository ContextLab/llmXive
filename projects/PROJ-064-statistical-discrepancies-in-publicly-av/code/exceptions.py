"""
Custom exception classes for the statistical discrepancies research pipeline.
These exceptions provide specific error types for different failure modes.
"""
from typing import Optional, Dict, Any


class DiscrepancyError(Exception):
    """Base exception for all discrepancy-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}


class DataAcquisitionError(DiscrepancyError):
    """Raised when data acquisition (download, parse) fails."""
    pass


class MissingDataError(DiscrepancyError):
    """Raised when required data fields are missing or incomplete."""
    pass


class ValidationFailureError(DiscrepancyError):
    """Raised when data validation checks fail."""
    pass


class StatisticalModelError(DiscrepancyError):
    """Raised when statistical modeling or simulation fails."""
    pass


class ConfigurationError(DiscrepancyError):
    """Raised when configuration files or parameters are invalid."""
    pass


class ReproducibilityError(DiscrepancyError):
    """Raised when reproducibility checks or verification fails."""
    pass
