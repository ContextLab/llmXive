"""Custom exceptions for the data loading and validation pipeline."""

class CriticalValidationError(Exception):
    """
    Raised when all fetched datasets fail validation (e.g., N < 50).
    This prevents pipeline deadlock by ensuring at least one valid dataset exists.
    """
    pass
