"""
Custom exceptions for the ball milling data pipeline.
"""

class DataIngestionError(Exception):
    """Raised when there is an error during data ingestion."""
    pass

class SourceConnectionError(DataIngestionError):
    """Raised when a connection to a data source fails."""
    pass

class SourceAuthenticationError(DataIngestionError):
    """Raised when authentication with a data source fails."""
    pass

class SourceNotFoundError(DataIngestionError):
    """Raised when a specified data source is not found."""
    pass

class DataFormatError(DataIngestionError):
    """Raised when data format is invalid or unexpected."""
    pass

class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""
    pass

class InsufficientDataError(Exception):
    """Raised when the dataset does not meet minimum size requirements."""
    pass

class GPRResourceLimitExceeded(Exception):
    """Raised when GPR training exceeds resource limits."""
    def __init__(self, runtime_seconds: float, memory_gb: float):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        super().__init__(
            f"GPR training exceeded limits: {runtime_seconds:.2f}s runtime, "
            f"{memory_gb:.2f}GB memory."
        )
