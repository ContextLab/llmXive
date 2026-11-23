"""
Unified Error Factory and Custom Exceptions.
Provides DataSchemaError and factory functions for standardized error messages.
"""
from typing import Optional

class DataSchemaError(Exception):
    """
    Custom exception for data schema validation failures.
    Standardized message format: "Missing required dataset or column: {source}/{column}"
    """
    def __init__(self, message: str, source: Optional[str] = None, column: Optional[str] = None):
        if source and column:
            full_message = f"Missing required dataset or column: {source}/{column}"
        else:
            full_message = message
        super().__init__(full_message)
        self.source = source
        self.column = column

class ConfigurationError(Exception):
    """Exception for configuration issues."""
    pass

class ModelInferenceError(Exception):
    """Exception for model inference failures."""
    pass

def create_missing_dataset_error(source: str, column: str) -> DataSchemaError:
    """
    Factory function to create a DataSchemaError with the standardized message.
    """
    return DataSchemaError(source=source, column=column)

def create_configuration_error(message: str) -> ConfigurationError:
    """Factory for configuration errors."""
    return ConfigurationError(message)

def create_model_inference_error(message: str) -> ModelInferenceError:
    """Factory for model inference errors."""
    return ModelInferenceError(message)
