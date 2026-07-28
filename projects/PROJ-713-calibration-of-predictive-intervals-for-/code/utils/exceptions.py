"""
Custom exception classes for the project.
"""
from typing import Optional, Dict, Any

class BaseProjectError(Exception):
    """Base exception for all project-specific errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DataFetchError(BaseProjectError):
    """Error raised when data fetching fails."""
    pass

class ModelConvergenceError(BaseProjectError):
    """Error raised when a model fails to converge."""
    pass

class CalibrationError(BaseProjectError):
    """Error raised during calibration computations."""
    pass

class DataValidationError(BaseProjectError):
    """Error raised when data validation fails."""
    pass

class ConfigurationError(BaseProjectError):
    """Error raised when configuration is invalid."""
    pass
