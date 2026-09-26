"""
Error definitions and factories for the llmXive pipeline.
Provides standardized error messages for schema and data validation failures.
"""
from typing import Optional


class DataSchemaError(Exception):
    """
    Raised when a required dataset or column is missing, or when schema validation fails.
    """
    pass


class ConfigurationError(Exception):
    """
    Raised when a configuration issue prevents pipeline execution.
    """
    pass


class ModelInferenceError(Exception):
    """
    Raised when a model inference step fails (e.g., timeout, model load failure).
    """
    pass


def create_missing_dataset_error(source: str, column: str) -> str:
    """
    Generates a standardized error message for missing dataset or column requirements.

    Args:
        source: The name of the dataset or source (e.g., 'pick-a-pic').
        column: The name of the missing column (e.g., 'human_rating').

    Returns:
        A formatted error string: "Missing required dataset or column: {source}/{column}"
    """
    return f"Missing required dataset or column: {source}/{column}"


def create_configuration_error(message: str) -> str:
    """
    Generates a standardized configuration error message.

    Args:
        message: The specific configuration issue description.

    Returns:
        A formatted error string.
    """
    return f"Configuration Error: {message}"


def create_model_inference_error(reason: str, details: Optional[str] = None) -> str:
    """
    Generates a standardized model inference error message.

    Args:
        reason: The primary reason for failure (e.g., 'TIMEOUT_EXCEEDED', 'BERT_FAILURE').
        details: Optional additional context.

    Returns:
        A formatted error string.
    """
    if details:
        return f"Model Inference Error ({reason}): {details}"
    return f"Model Inference Error ({reason})"