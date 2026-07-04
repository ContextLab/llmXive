from typing import Optional, Dict, Any

class BaseProjectError(Exception):
    """Base exception for all project-specific errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class DataFetchError(BaseProjectError):
    """Raised when data fetching fails."""
    pass

class ModelConvergenceError(BaseProjectError):
    """Raised when a model fails to converge."""
    pass

class CalibrationError(BaseProjectError):
    """Raised when calibration metrics cannot be computed."""
    pass

class DataValidationError(BaseProjectError):
    """Raised when data validation fails."""
    pass

class ConfigurationError(BaseProjectError):
    """Raised when configuration is invalid."""
    pass
