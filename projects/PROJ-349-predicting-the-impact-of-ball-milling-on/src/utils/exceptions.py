"""
Custom exceptions for the ball milling data pipeline.

This module defines specific exception classes used throughout the project
to handle various error conditions in a structured way.
"""

class DataIngestionError(Exception):
    """Raised when there is an error during data ingestion from a source."""
    pass


class MissingTimestampError(Exception):
    """Raised when a required timestamp is missing from the data."""
    pass


class GPRResourceLimitExceeded(Exception):
    """Raised when GPR training exceeds configured resource limits (time/memory)."""
    def __init__(self, runtime_seconds: float, memory_gb: float):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        message = (
            f"GPR training exceeded limits: "
            f"Runtime: {runtime_seconds:.2f}s (limit exceeded), "
            f"Memory: {memory_gb:.2f}GB (limit exceeded)."
        )
        super().__init__(message)


class InsufficientDataError(Exception):
    """
    Raised when the dataset does not meet minimum data requirements
    (e.g., missing required fields, null values in required columns,
    or insufficient row count when enforced).
    """
    pass


class SchemaValidationError(Exception):
    """Raised when data validation against the schema fails."""
    pass


class MissingDataError(Exception):
    """Raised when a specific required data point is missing and cannot be imputed."""
    pass