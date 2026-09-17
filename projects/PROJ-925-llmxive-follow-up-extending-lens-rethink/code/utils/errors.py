"""
Unified error handling utilities for the llmXive pipeline.

This module provides standardized error classes and factory functions
to ensure consistent error messaging across the project, enforcing
the "Single Source of Truth" principle for error handling.
"""
from typing import Optional


class DataSchemaError(Exception):
    """
    Exception raised when dataset or schema validation fails.
    
    This error is used to indicate missing required datasets, columns,
    or schema mismatches. It enforces a unified error message format.
    """
    pass


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


class ModelInferenceError(Exception):
    """Exception raised when model inference fails."""
    pass


def create_missing_dataset_error(source: str, column: str) -> DataSchemaError:
    """
    Factory function to create a standardized DataSchemaError.
    
    This function ensures that all missing dataset/column errors
    follow the unified message pattern required by the contracts.
    
    Args:
        source: The dataset or data source name (e.g., 'pick-a-pic')
        column: The missing column name (e.g., 'human_rating')
        
    Returns:
        DataSchemaError with the standardized message format:
        "Missing required dataset or column: {source}/{column}"
    """
    message = f"Missing required dataset or column: {source}/{column}"
    return DataSchemaError(message)


def create_configuration_error(message: str) -> ConfigurationError:
    """
    Factory function to create a standardized ConfigurationError.
    
    Args:
        message: The error description
        
    Returns:
        ConfigurationError with the provided message
    """
    return ConfigurationError(message)


def create_model_inference_error(message: str) -> ModelInferenceError:
    """
    Factory function to create a standardized ModelInferenceError.
    
    Args:
        message: The error description
        
    Returns:
        ModelInferenceError with the provided message
    """
    return ModelInferenceError(message)