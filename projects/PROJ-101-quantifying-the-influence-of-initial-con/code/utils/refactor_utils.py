"""
Utility functions for numerical stability, validation, and data processing.

This module provides helper functions for safe arithmetic operations,
input validation, and data normalization used across the analysis pipeline.
"""
from typing import Optional, List, Tuple, Any, Dict, Union
from dataclasses import dataclass, field
import logging
import numpy as np
import time
from functools import wraps

# Configure logging for this module
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Container for validation results and error messages."""
    is_valid: bool
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success(cls, message: str = "Validation passed", details: Optional[Dict] = None) -> "ValidationResult":
        return cls(is_valid=True, message=message, details=details or {})

    @classmethod
    def failure(cls, message: str, details: Optional[Dict] = None) -> "ValidationResult":
        return cls(is_valid=False, message=message, details=details or {})


def safe_divide(
    numerator: Union[float, np.ndarray],
    denominator: Union[float, np.ndarray],
    default: float = 0.0,
    epsilon: float = 1e-12
) -> Union[float, np.ndarray]:
    """
    Safely divide two numbers, avoiding division by zero.

    Args:
        numerator: The numerator value or array.
        denominator: The denominator value or array.
        default: The value to return when denominator is zero.
        epsilon: Threshold below which denominator is considered zero.

    Returns:
        The result of division, with zeros replaced by default value.
    """
    if isinstance(numerator, (int, float)) and isinstance(denominator, (int, float)):
        if abs(denominator) < epsilon:
            logger.debug(f"Division by near-zero detected: {numerator}/{denominator} -> {default}")
            return default
        return numerator / denominator

    # Handle numpy arrays
    numerator_arr = np.asarray(numerator)
    denominator_arr = np.asarray(denominator)

    result = np.full_like(numerator_arr, default, dtype=float)
    mask = np.abs(denominator_arr) >= epsilon
    result[mask] = numerator_arr[mask] / denominator_arr[mask]

    return result


def clamp(
    value: Union[float, np.ndarray],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None
) -> Union[float, np.ndarray]:
    """
    Clamp a value or array to a specified range.

    Args:
        value: The value or array to clamp.
        min_val: Minimum allowed value (None for no lower bound).
        max_val: Maximum allowed value (None for no upper bound).

    Returns:
        The clamped value or array.
    """
    if min_val is not None:
        value = np.maximum(value, min_val)
    if max_val is not None:
        value = np.minimum(value, max_val)
    return value


def format_float(
    value: float,
    precision: int = 6,
    scientific: bool = False,
    strip_zeros: bool = True
) -> str:
    """
    Format a float value for display.

    Args:
        value: The float value to format.
        precision: Number of decimal places.
        scientific: Use scientific notation.
        strip_zeros: Remove trailing zeros.

    Returns:
        Formatted string representation.
    """
    if scientific:
        formatted = f"{value:.{precision}e}"
    else:
        formatted = f"{value:.{precision}f}"

    if strip_zeros and not scientific:
        formatted = formatted.rstrip('0').rstrip('.')

    return formatted


def validate_positive(
    value: Union[float, np.ndarray],
    name: str = "value",
    strict: bool = True
) -> ValidationResult:
    """
    Validate that a value is positive.

    Args:
        value: The value to validate.
        name: Name of the parameter for error messages.
        strict: If True, zero is not allowed.

    Returns:
        ValidationResult indicating success or failure.
    """
    if isinstance(value, (int, float)):
        if strict:
            if value <= 0:
                return ValidationResult.failure(f"{name} must be positive, got {value}")
        else:
            if value < 0:
                return ValidationResult.failure(f"{name} must be non-negative, got {value}")
        return ValidationResult.success(f"{name} is valid: {value}")

    # Handle arrays
    arr = np.asarray(value)
    if strict:
        if np.any(arr <= 0):
            return ValidationResult.failure(
                f"{name} contains non-positive values",
                details={"min_value": float(np.min(arr)), "count_non_positive": int(np.sum(arr <= 0))}
            )
    else:
        if np.any(arr < 0):
            return ValidationResult.failure(
                f"{name} contains negative values",
                details={"min_value": float(np.min(arr))}
            )
    return ValidationResult.success(f"{name} is valid (all positive)")


def validate_non_negative(
    value: Union[float, np.ndarray],
    name: str = "value"
) -> ValidationResult:
    """
    Validate that a value is non-negative.

    Args:
        value: The value to validate.
        name: Name of the parameter for error messages.

    Returns:
        ValidationResult indicating success or failure.
    """
    return validate_positive(value, name=name, strict=False)


def normalize_array(
    arr: np.ndarray,
    method: str = "minmax",
    axis: Optional[int] = None
) -> np.ndarray:
    """
    Normalize an array using specified method.

    Args:
        arr: Input array.
        method: Normalization method ('minmax', 'zscore', 'unit').
        axis: Axis along which to normalize (None for global).

    Returns:
        Normalized array.
    """
    arr = np.asarray(arr, dtype=float)

    if method == "minmax":
        min_val = arr.min(axis=axis, keepdims=True) if axis is not None else arr.min()
        max_val = arr.max(axis=axis, keepdims=True) if axis is not None else arr.max()
        range_val = max_val - min_val

        if np.any(range_val == 0):
            logger.warning("Range is zero, returning zeros")
            return np.zeros_like(arr)

        return (arr - min_val) / range_val

    elif method == "zscore":
        mean_val = arr.mean(axis=axis, keepdims=True) if axis is not None else arr.mean()
        std_val = arr.std(axis=axis, keepdims=True) if axis is not None else arr.std()

        if np.any(std_val == 0):
            logger.warning("Standard deviation is zero, returning zeros")
            return np.zeros_like(arr)

        return (arr - mean_val) / std_val

    elif method == "unit":
        norm = np.linalg.norm(arr)
        if norm == 0:
            return arr
        return arr / norm

    else:
        raise ValueError(f"Unknown normalization method: {method}")


def batch_process(
    items: List[Any],
    processor_func,
    batch_size: int = 100,
    show_progress: bool = False
) -> List[Any]:
    """
    Process a list of items in batches.

    Args:
        items: List of items to process.
        processor_func: Function to apply to each item.
        batch_size: Number of items per batch.
        show_progress: Whether to log progress.

    Returns:
        List of processed results.
    """
    results = []
    total = len(items)

    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        batch_results = [processor_func(item) for item in batch]
        results.extend(batch_results)

        if show_progress:
            logger.info(f"Processed {min(i + batch_size, total)}/{total} items")

    return results


def merge_dicts(
    *dicts: Dict[str, Any],
    overwrite: bool = True
) -> Dict[str, Any]:
    """
    Merge multiple dictionaries into one.

    Args:
        *dicts: Dictionaries to merge.
        overwrite: If True, later values overwrite earlier ones.

    Returns:
        Merged dictionary.
    """
    result = {}
    for d in dicts:
        for key, value in d.items():
            if key in result and overwrite:
                result[key] = value
            elif key not in result:
                result[key] = value
    return result


def get_safe_value(
    dictionary: Dict[str, Any],
    key: str,
    default: Any = None,
    required: bool = False
) -> Any:
    """
    Safely get a value from a dictionary.

    Args:
        dictionary: The dictionary to query.
        key: The key to look up.
        default: Default value if key is missing.
        required: If True, raise KeyError when missing.

    Returns:
        The value or default.

    Raises:
        KeyError: If required is True and key is missing.
    """
    if key in dictionary:
        return dictionary[key]
    if required:
        raise KeyError(f"Required key '{key}' not found in dictionary")
    return default


def log_execution_time(func):
    """
    Decorator to log the execution time of a function.

    Args:
        func: The function to wrap.

    Returns:
        Wrapped function with timing.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        logger.info(f"{func.__name__} executed in {elapsed:.4f} seconds")
        return result
    return wrapper


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path.

    Returns:
        The Path object.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_input_type(
    value: Any,
    expected_type: type,
    name: str = "input"
) -> ValidationResult:
    """
    Validate that a value is of the expected type.

    Args:
        value: The value to check.
        expected_type: The expected type.
        name: Name of the parameter for error messages.

    Returns:
        ValidationResult indicating success or failure.
    """
    if isinstance(value, expected_type):
        return ValidationResult.success(f"{name} is of type {expected_type.__name__}")
    return ValidationResult.failure(
        f"{name} must be {expected_type.__name__}, got {type(value).__name__}",
        details={"actual_type": type(value).__name__}
    )


def summarize_array(
    arr: np.ndarray,
    name: str = "array"
) -> Dict[str, Any]:
    """
    Generate a summary of an array's statistics.

    Args:
        arr: The input array.
        name: Name of the array for the summary.

    Returns:
        Dictionary with summary statistics.
    """
    arr = np.asarray(arr)
    return {
        "name": name,
        "shape": arr.shape,
        "dtype": str(arr.dtype),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "nan_count": int(np.sum(np.isnan(arr))),
        "inf_count": int(np.sum(np.isinf(arr)))
    }
