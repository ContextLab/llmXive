"""
Custom exceptions for the plant disease resistance prediction pipeline.

This module defines all custom exception classes used throughout the project
to ensure consistent error handling and clear error messages.
"""

class DataFetchError(Exception):
    """Raised when data fetching from external sources fails."""
    pass

class DataUnavailableError(Exception):
    """Raised when required data files are missing or unavailable."""
    pass

class DataAvailabilityError(Exception):
    """Raised when no studies meet the required metadata criteria."""
    pass

class TemporalVerificationError(Exception):
    """Raised when temporal validation fails completely (no studies verified)."""
    pass

class TemporalVerificationWarning(Warning):
    """Warning for individual studies with ambiguous temporal metadata."""
    pass

class BatchCorrectionFailureError(Exception):
    """Raised when batch correction (e.g., ComBat) fails to converge."""
    pass

class DataAlignmentError(Exception):
    """Raised when metabolite alignment fails due to insufficient intersection."""
    pass

class ClassImbalanceError(Exception):
    """Raised when class imbalance is detected in validation splits."""
    pass

class PathwayMappingWarning(Warning):
    """Warning for pathway mapping issues (e.g., API timeouts, low success rate)."""
    pass
