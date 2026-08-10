"""
Custom exception hierarchy for the Statistical Discrepancies project.
"""
class DiscrepancyError(Exception):
    """Base exception for all project-specific errors."""
    pass

class DataAcquisitionError(DiscrepancyError):
    """Raised when data download or initial parsing fails."""
    pass

class MissingDataError(DiscrepancyError):
    """Raised when required data columns or rows are missing."""
    pass

class ValidationFailureError(DiscrepancyError):
    """Raised when data validation constraints are violated."""
    pass

class StatisticalModelError(DiscrepancyError):
    """Raised when statistical model fitting or simulation fails."""
    pass

class ConfigurationError(DiscrepancyError):
    """Raised when configuration files are malformed or missing required keys."""
    pass
