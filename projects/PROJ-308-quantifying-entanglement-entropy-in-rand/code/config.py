"""
Configuration module for the entanglement entropy project.

Provides strict input validation for simulation parameters:
- System size L (20-40)
- Disorder strength delta (0-1)
- Number of realizations N_real (50-200)
- Random seed (non-negative integer)

Raises ValueError with clear messages for out-of-bounds parameters.
"""

import os
from typing import Optional


class ConfigError(ValueError):
    """Custom exception for configuration validation errors."""
    pass


def validate_int(value: int, min_val: int, max_val: int, param_name: str) -> int:
    """
    Validate that an integer parameter is within the specified range.

    Args:
        value: The value to validate.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        param_name: Name of the parameter for error messages.

    Returns:
        The validated integer value.

    Raises:
        ConfigError: If the value is not an integer or is out of bounds.
    """
    if not isinstance(value, int):
        raise ConfigError(
            f"Parameter '{param_name}' must be an integer, got {type(value).__name__}."
        )
    if value < min_val or value > max_val:
        raise ConfigError(
            f"Parameter '{param_name}' must be between {min_val} and {max_val} (inclusive). "
            f"Got {value}."
        )
    return value


def validate_float(value: float, min_val: float, max_val: float, param_name: str) -> float:
    """
    Validate that a float parameter is within the specified range.

    Args:
        value: The value to validate.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        param_name: Name of the parameter for error messages.

    Returns:
        The validated float value.

    Raises:
        ConfigError: If the value is not a float/int or is out of bounds.
    """
    if not isinstance(value, (int, float)):
        raise ConfigError(
            f"Parameter '{param_name}' must be a number, got {type(value).__name__}."
        )
    if value < min_val or value > max_val:
        raise ConfigError(
            f"Parameter '{param_name}' must be between {min_val} and {max_val} (inclusive). "
            f"Got {value}."
        )
    return float(value)


def validate_random_seed(value: Optional[int]) -> int:
    """
    Validate the random seed.

    Args:
        value: The seed value. If None, generates a random seed.

    Returns:
        A valid non-negative integer seed.

    Raises:
        ConfigError: If the seed is negative.
    """
    if value is None:
        import random
        return random.randint(0, 2**32 - 1)

    if not isinstance(value, int):
        raise ConfigError(
            f"Parameter 'random_seed' must be an integer or None, got {type(value).__name__}."
        )
    if value < 0:
        raise ConfigError(
            f"Parameter 'random_seed' must be non-negative, got {value}."
        )
    return value


def validate_config(
    L: int,
    delta: float,
    N_real: int,
    random_seed: Optional[int] = None
) -> dict:
    """
    Validate all simulation parameters according to project constraints.

    Args:
        L: System size (chain length). Must be in [20, 40].
        delta: Disorder strength. Must be in [0, 1].
        N_real: Number of disorder realizations. Must be in [50, 200].
        random_seed: Random seed for reproducibility. Must be non-negative or None.

    Returns:
        A dictionary containing the validated parameters.

    Raises:
        ConfigError: If any parameter is out of bounds or invalid.
    """
    # Validate L
    L_validated = validate_int(L, min_val=20, max_val=40, param_name="L")

    # Validate delta
    delta_validated = validate_float(delta, min_val=0.0, max_val=1.0, param_name="delta")

    # Validate N_real
    N_real_validated = validate_int(N_real, min_val=50, max_val=200, param_name="N_real")

    # Validate random_seed
    seed_validated = validate_random_seed(random_seed)

    return {
        "L": L_validated,
        "delta": delta_validated,
        "N_real": N_real_validated,
        "random_seed": seed_validated
    }


def get_default_config() -> dict:
    """
    Return a dictionary of default configuration values.

    Returns:
        Dictionary with default parameters.
    """
    return {
        "L": 30,
        "delta": 0.2,
        "N_real": 100,
        "random_seed": None  # Will generate a random seed if None
    }
