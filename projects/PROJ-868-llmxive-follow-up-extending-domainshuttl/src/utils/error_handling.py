"""
Error handling utilities for the llmXive pipeline.

This module enforces the "FAIL LOUDLY" policy:
- No synthetic fallbacks for data loading or model inference.
- All errors are propagated as specific, actionable exceptions.
"""

import logging
from typing import Callable, TypeVar, Optional, Union
from functools import wraps

# Custom Exceptions
class DataLoadError(RuntimeError):
    """Raised when real data loading fails without a valid fallback."""
    pass

class ModelInferenceError(RuntimeError):
    """Raised when model inference fails."""
    pass

class ConfigurationError(RuntimeError):
    """Raised when configuration is missing or invalid."""
    pass

T = TypeVar('T')

logger = logging.getLogger(__name__)

def fail_loudly_on_data_load(
    func: Callable[..., T]
) -> Callable[..., T]:
    """
    Decorator to enforce "FAIL LOUDLY" policy for data loading functions.

    If the wrapped function fails to load real data, it raises a DataLoadError
    instead of falling back to synthetic data or returning None.

    Args:
        func: The data loading function to wrap.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            logger.info(f"Attempting to load data via {func.__name__}...")
            result = func(*args, **kwargs)
            if result is None:
                raise DataLoadError(
                    f"{func.__name__} returned None. "
                    "Real data fetch failed and no synthetic fallback is allowed."
                )
            logger.info(f"Successfully loaded data via {func.__name__}.")
            return result
        except DataLoadError:
            # Re-raise DataLoadError as-is
            raise
        except Exception as e:
            # Catch any other exception and wrap it in DataLoadError
            logger.error(
                f"Data loading failed in {func.__name__} with error: {str(e)}. "
                "Raising DataLoadError (no synthetic fallback)."
            )
            raise DataLoadError(
                f"Failed to load real data in {func.__name__}: {str(e)}. "
                "No synthetic fallback available."
            ) from e
    return wrapper

def fail_loudly_on_inference(
    func: Callable[..., T]
) -> Callable[..., T]:
    """
    Decorator to enforce "FAIL LOUDLY" policy for model inference functions.

    If the wrapped function fails during inference, it raises a ModelInferenceError
    instead of returning dummy outputs.

    Args:
        func: The inference function to wrap.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        try:
            logger.info(f"Starting model inference via {func.__name__}...")
            result = func(*args, **kwargs)
            if result is None:
                raise ModelInferenceError(
                    f"{func.__name__} returned None. "
                    "Inference failed and no dummy output is allowed."
                )
            logger.info(f"Successfully completed inference via {func.__name__}.")
            return result
        except ModelInferenceError:
            # Re-raise ModelInferenceError as-is
            raise
        except Exception as e:
            # Catch any other exception and wrap it in ModelInferenceError
            logger.error(
                f"Inference failed in {func.__name__} with error: {str(e)}. "
                "Raising ModelInferenceError (no dummy fallback)."
            )
            raise ModelInferenceError(
                f"Failed during model inference in {func.__name__}: {str(e)}. "
                "No dummy output available."
            ) from e
    return wrapper

def validate_config_key(
    config: dict,
    key: str,
    expected_type: Optional[type] = None,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None
) -> None:
    """
    Validate a configuration key exists and meets constraints.

    Args:
        config: The configuration dictionary.
        key: The key to validate.
        expected_type: Optional type the value must match.
        min_value: Optional minimum numeric value.
        max_value: Optional maximum numeric value.

    Raises:
        ConfigurationError: If the key is missing, wrong type, or out of range.
    """
    if key not in config:
        raise ConfigurationError(
            f"Configuration key '{key}' is missing. "
            "This is required for the pipeline to proceed."
        )

    value = config[key]

    if expected_type and not isinstance(value, expected_type):
        raise ConfigurationError(
            f"Configuration key '{key}' has type {type(value).__name__}, "
            f"expected {expected_type.__name__}."
        )

    if isinstance(value, (int, float)):
        if min_value is not None and value < min_value:
            raise ConfigurationError(
                f"Configuration key '{key}' value {value} is below minimum {min_value}."
            )
        if max_value is not None and value > max_value:
            raise ConfigurationError(
                f"Configuration key '{key}' value {value} is above maximum {max_value}."
            )

class LoudFailureContext:
    """
    Context manager to enforce loud failures within a block of code.

    Usage:
        with LoudFailureContext("Operation X"):
            # Code that must not fail silently
            result = do_something()
    """
    def __init__(self, operation_name: str):
        self.operation_name = operation_name

    def __enter__(self):
        logger.info(f"Entering loud failure context: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"Loud failure in {self.operation_name}: {str(exc_val)}. "
                "Error will propagate."
            )
            # Do not suppress the exception
            return False
        logger.info(f"Successfully exited loud failure context: {self.operation_name}")
        return False

# Export public API
__all__ = [
    'DataLoadError',
    'ModelInferenceError',
    'ConfigurationError',
    'fail_loudly_on_data_load',
    'fail_loudly_on_inference',
    'validate_config_key',
    'LoudFailureContext'
]