"""
Custom exceptions for the llmXive research pipeline.
"""

class DataIngestionError(Exception):
    """Raised when an error occurs during data ingestion."""
    pass

class MissingTimestampError(Exception):
    """Raised when a required timestamp is missing."""
    pass

class GPRResourceLimitExceeded(Exception):
    """Raised when GPR training exceeds resource limits."""
    def __init__(self, runtime_seconds, memory_gb):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        super().__init__(f"GPR exceeded limits: {runtime_seconds}s runtime, {memory_gb}GB memory")

class InsufficientDataError(Exception):
    """Raised when there is insufficient data for processing."""
    pass

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass

class SourceConnectionError(Exception):
    """Raised when a connection to a data source fails."""
    pass

class SourceAuthenticationError(Exception):
    """Raised when authentication to a data source fails."""
    pass

class SourceNotFoundError(Exception):
    """Raised when a data source is not found."""
    pass

class DataFormatError(Exception):
    """Raised when data format is invalid."""
    pass

class StratificationError(Exception):
    """Raised when stratification fails."""
    pass
