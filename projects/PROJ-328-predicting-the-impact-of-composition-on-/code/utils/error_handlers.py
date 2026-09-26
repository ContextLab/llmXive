"""
Custom exception handlers for the pipeline.
"""

class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass


class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass


class FramingViolationError(Exception):
    """Raised when causal language is detected in associational analysis."""
    pass
