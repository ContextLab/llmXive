"""
Custom exceptions for the llmXive pipeline.
"""
class DataIngestionError(Exception):
    """Raised when data ingestion fails."""
    pass

class SourceConnectionError(Exception):
    """Raised when a connection to a data source fails."""
    pass

class SourceAuthenticationError(Exception):
    """Raised when authentication with a data source fails."""
    pass

class SourceNotFoundError(Exception):
    """Raised when a requested data source is not found."""
    pass

class DataFormatError(Exception):
    """Raised when data format is invalid."""
    pass

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass

class InsufficientDataError(Exception):
    """Raised when the dataset does not meet minimum size requirements."""
    pass

class GPRResourceLimitExceeded(Exception):
    """Raised when GPR training exceeds resource limits."""
    pass
