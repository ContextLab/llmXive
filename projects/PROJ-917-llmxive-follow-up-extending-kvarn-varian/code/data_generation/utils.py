"""
Numerical stability utilities for the llmXive pipeline.

This module provides functions for:
- Epsilon floor handling to prevent division by zero and log(0).
- Temporal drift models for synthetic data generation.
- Numerical stability checks (NaN, Inf).
"""
import numpy as np
from typing import Union, Optional, Callable
import json
import hashlib
from pathlib import Path

# Default epsilon for numerical stability
DEFAULT_EPSILON = 1e-8

def apply_epsilon_floor(
    arr: Union[np.ndarray, float],
    epsilon: Optional[float] = None
) -> np.ndarray:
    """
    Apply an epsilon floor to an array or scalar to prevent values from being
    too close to zero (e.g., for variance or probabilities).

    Args:
        arr: Input array or scalar.
        epsilon: The floor value. Defaults to DEFAULT_EPSILON.

    Returns:
        A numpy array (or scalar if input was scalar) with values clamped
        to be >= epsilon.
    """
    if epsilon is None:
        epsilon = DEFAULT_EPSILON

    input_is_scalar = np.isscalar(arr)
    arr = np.asarray(arr, dtype=np.float64)

    result = np.maximum(arr, epsilon)

    if input_is_scalar:
        return float(result)
    return result

def safe_log(
    arr: Union[np.ndarray, float],
    epsilon: Optional[float] = None
) -> np.ndarray:
    """
    Compute the natural logarithm safely by applying an epsilon floor first.

    Args:
        arr: Input array or scalar.
        epsilon: The floor value applied before log.

    Returns:
        The natural logarithm of the input, with values >= epsilon.
    """
    safe_arr = apply_epsilon_floor(arr, epsilon)
    return np.log(safe_arr)

def safe_divide(
    numerator: Union[np.ndarray, float],
    denominator: Union[np.ndarray, float],
    epsilon: Optional[float] = None
) -> np.ndarray:
    """
    Perform safe division by applying an epsilon floor to the denominator.

    Args:
        numerator: Numerator array or scalar.
        denominator: Denominator array or scalar.
        epsilon: The floor value applied to the denominator.

    Returns:
        The result of numerator / denominator.
    """
    safe_denom = apply_epsilon_floor(denominator, epsilon)
    return np.asarray(numerator) / safe_denom

def check_numerical_stability(
    arr: np.ndarray,
    name: str = "array"
) -> bool:
    """
    Check an array for NaN and Inf values.

    Args:
        arr: The array to check.
        name: A name for the array (for error messages).

    Returns:
        True if the array is stable (no NaN or Inf), False otherwise.
    """
    if np.any(np.isnan(arr)):
        raise ValueError(f"NaN values detected in {name}")
    if np.any(np.isinf(arr)):
        raise ValueError(f"Inf values detected in {name}")
    return True

# --- Drift Models ---

def linear_drift(
    t: Union[np.ndarray, float],
    slope: float = 0.01,
    intercept: float = 1.0
) -> np.ndarray:
    """
    Generate a linear drift over time.

    Args:
        t: Time steps (scalar or array).
        slope: The slope of the drift.
        intercept: The starting value at t=0.

    Returns:
        Drifted values.
    """
    t = np.asarray(t, dtype=np.float64)
    return slope * t + intercept

def exponential_drift(
    t: Union[np.ndarray, float],
    rate: float = 0.01,
    initial: float = 1.0
) -> np.ndarray:
    """
    Generate an exponential drift over time.

    Args:
        t: Time steps (scalar or array).
        rate: The growth/decay rate.
        initial: The starting value at t=0.

    Returns:
        Drifted values.
    """
    t = np.asarray(t, dtype=np.float64)
    return initial * np.exp(rate * t)

def sinusoidal_drift(
    t: Union[np.ndarray, float],
    amplitude: float = 0.5,
    frequency: float = 0.1,
    phase: float = 0.0,
    offset: float = 1.0
) -> np.ndarray:
    """
    Generate a sinusoidal drift over time.

    Args:
        t: Time steps (scalar or array).
        amplitude: Amplitude of the sine wave.
        frequency: Frequency of the sine wave.
        phase: Phase shift.
        offset: Vertical offset (mean value).

    Returns:
        Drifted values.
    """
    t = np.asarray(t, dtype=np.float64)
    return offset + amplitude * np.sin(2 * np.pi * frequency * t + phase)

def get_drift_model(name: str) -> Callable:
    """
    Retrieve a drift model function by name.

    Args:
        name: One of 'linear', 'exponential', 'sinusoidal'.

    Returns:
        The corresponding drift function.

    Raises:
        ValueError: If the name is not recognized.
    """
    models = {
        'linear': linear_drift,
        'exponential': exponential_drift,
        'sinusoidal': sinusoidal_drift
    }
    if name not in models:
        raise ValueError(f"Unknown drift model: {name}. Choose from {list(models.keys())}")
    return models[name]

def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_json_with_checksum(data: dict, output_path: Union[str, Path]) -> None:
    """
    Save a dictionary to JSON and compute its checksum.

    Args:
        data: The dictionary to save.
        output_path: Path to the output file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    checksum = compute_checksum(output_path)
    return checksum