"""
Custom exceptions for the ball milling data pipeline.
Used for consistent error handling across ingestion, validation, and modeling.
"""

class DataIngestionError(Exception):
    """Base exception for data ingestion failures."""
    def __init__(self, message: str, source: str = None):
        self.source = source
        super().__init__(f"[{source or 'Unknown'}] {message}")


class SourceConnectionError(DataIngestionError):
    """Raised when a data source connection fails."""
    pass


class SourceAuthenticationError(DataIngestionError):
    """Raised when authentication with a data source fails."""
    pass


class SourceNotFoundError(DataIngestionError):
    """Raised when a requested data source or resource is not found."""
    pass


class DataFormatError(DataIngestionError):
    """Raised when data format is invalid or unexpected."""
    pass


class SchemaValidationError(DataIngestionError):
    """Raised when data fails schema validation."""
    def __init__(self, message: str, violations: list = None):
        self.violations = violations or []
        super().__init__(message)


class InsufficientDataError(DataIngestionError):
    """Raised when the dataset does not meet minimum size requirements."""
    def __init__(self, message: str, current_count: int = 0, minimum_required: int = 150):
        self.current_count = current_count
        self.minimum_required = minimum_required
        super().__init__(f"{message} (Current: {current_count}, Required: {minimum_required})")


class MissingTimestampError(DataIngestionError):
    """Raised when critical timestamp data is missing and cannot be imputed."""
    pass


class GPRResourceLimitExceeded(Exception):
    """
    Raised when Gaussian Process Regression training exceeds configured
    runtime or memory limits.
    
    Attributes:
        runtime_seconds: Actual runtime in seconds
        memory_gb: Actual memory usage in GB
    """
    def __init__(self, runtime_seconds: float, memory_gb: float):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        message = (
            f"GPR training exceeded limits: "
            f"Runtime {runtime_seconds:.2f}s (limit: configured), "
            f"Memory {memory_gb:.2f}GB (limit: configured)"
        )
        super().__init__(message)
