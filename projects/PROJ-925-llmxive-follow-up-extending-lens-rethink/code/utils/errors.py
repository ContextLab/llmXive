"""
Custom exceptions for the llmXive pipeline.
"""
class DataSchemaError(Exception):
    """Raised when dataset schema validation fails (missing columns, wrong types, etc.)."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass

class ModelInferenceError(Exception):
    """Raised when model inference fails."""
    pass
