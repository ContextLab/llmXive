"""
Deterministic seed setting utilities for reproducible experiments.

This module ensures that all random number generation in the pipeline
is deterministic by setting seeds for numpy and the Python random module.
"""

import random
from typing import Optional

import numpy as np


def set_seed(seed: int = 42) -> None:
    """
    Set the random seed for reproducibility across the pipeline.

    This function sets the seed for:
    - Python's built-in `random` module
    - `numpy` random number generator

    Args:
        seed (int): The integer seed value. Defaults to 42.

    Example:
        >>> set_seed(123)
        >>> # Subsequent random operations will be deterministic
    """
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be an integer, got {type(seed).__name__}")

    random.seed(seed)
    np.random.seed(seed)


def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """
    Create a new NumPy random Generator instance with a specific seed.

    This is useful when you need an isolated random state for a specific
    operation (e.g., a single cross-validation fold) without affecting
    the global random state.

    Args:
        seed (int, optional): The seed value. If None, uses a random seed.

    Returns:
        np.random.Generator: A configured NumPy random Generator.

    Example:
        >>> rng = get_rng(42)
        >>> samples = rng.normal(0, 1, 100)
    """
    if seed is not None:
        return np.random.default_rng(seed)
    return np.random.default_rng()