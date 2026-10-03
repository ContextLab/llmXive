"""
Custom error handlers for the ingestion pipeline.
"""
class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

class PipelineError(Exception):
    """Raised when pipeline execution fails."""
    pass
