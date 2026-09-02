"""
Custom exceptions for the data pipeline.
"""

class DataUnavailableError(Exception):
    """Raised when required data is missing or cannot be fetched."""
    pass

class TemporalVerificationError(Exception):
    """Raised when temporal consistency checks fail."""
    pass
