"""
Custom exception classes for the llmXive pipeline.
"""

class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""
    pass


class ConfigurationError(PipelineError):
    """Raised when there is an issue with configuration settings."""
    pass


class DataError(PipelineError):
    """Raised when there is an issue with data loading or processing."""
    pass
