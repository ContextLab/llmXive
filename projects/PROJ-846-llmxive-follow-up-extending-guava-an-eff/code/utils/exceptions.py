"""
Custom exceptions for the llmXive research pipeline.

These exceptions are used to enforce strict error handling and
prevent silent failures in the research pipeline.
"""

class LlmXiveError(Exception):
    """Base exception for llmXive pipeline errors."""
    pass

class DatasetUnavailableError(LlmXiveError):
    """
    Raised when a required dataset or data file is missing or inaccessible.
    
    This exception enforces the "fail loudly" constraint: if real data
    cannot be fetched or loaded, the pipeline must stop rather than
    falling back to synthetic or placeholder data.
    """
    pass

class PerceptionInferenceError(LlmXiveError):
    """Raised when object detection or perception inference fails."""
    pass

class SymbolicTransformationError(LlmXiveError):
    """Raised when transformation from raw data to symbolic state fails."""
    pass

class ValidationThresholdError(LlmXiveError):
    """Raised when a validation metric fails to meet a required threshold."""
    pass