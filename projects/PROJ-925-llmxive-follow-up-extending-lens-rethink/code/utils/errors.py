"""
Custom exception classes for the llmXive project.

Defines specific error types for schema validation, configuration, and model inference.
"""

class DataSchemaError(Exception):
    """
    Raised when a dataset or schema validation fails.
    
    This error is used to enforce strict data contracts (FR-003).
    It specifically handles missing datasets or columns.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ConfigurationError(Exception):
    """
    Raised when there is an error in project configuration.
    
    Examples: Missing config file, invalid seed, incorrect path settings.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ModelInferenceError(Exception):
    """
    Raised when model inference fails (e.g., timeout, model loading error).
    
    Used to distinguish between data issues and model/runtime issues.
    """
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
