"""
Custom exception classes for the election discrepancy analysis project.
"""
from typing import Optional, Dict, Any

class DiscrepancyError(Exception):
    """Base exception for discrepancy analysis errors."""
    pass

class DataAcquisitionError(Exception):
    """Raised when data download or parsing fails."""
    pass

class MissingDataError(Exception):
    """Raised when required data fields are missing."""
    pass

class ValidationFailureError(Exception):
    """Raised when data validation fails."""
    pass

class StatisticalModelError(Exception):
    """Raised when statistical model fitting fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration or source verification fails."""
    pass

class ReproducibilityError(Exception):
    """Raised when reproducibility checks fail."""
    pass
