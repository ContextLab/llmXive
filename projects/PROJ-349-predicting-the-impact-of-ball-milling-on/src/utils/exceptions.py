"""
Custom exceptions for the ball milling prediction pipeline.
"""

class DataIngestionError(Exception):
    """Exception raised for errors during data ingestion."""
    pass

class MissingTimestampError(Exception):
    """Exception raised when a required timestamp is missing."""
    pass

class GPRResourceLimitExceeded(Exception):
    """Exception raised when GPR training exceeds resource limits."""
    def __init__(self, runtime_seconds: float, memory_gb: float):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        super().__init__(
            f"GPR training exceeded limits: {runtime_seconds:.2f}s runtime, "
            f"{memory_gb:.2f}GB memory"
        )

class InsufficientDataError(Exception):
    """Exception raised when there is insufficient data for processing."""
    pass

class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass

class SourceConnectionError(Exception):
    """Exception raised when a data source connection fails."""
    pass

class SourceAuthenticationError(Exception):
    """Exception raised when source authentication fails."""
    pass

class SourceNotFoundError(Exception):
    """Exception raised when a data source is not found."""
    pass

class DataFormatError(Exception):
    """Exception raised when data format is invalid."""
    pass

class StratificationError(Exception):
    """Exception raised when stratification fails."""
    pass
