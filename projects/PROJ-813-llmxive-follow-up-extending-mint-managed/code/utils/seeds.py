"""
Deterministic random seed management for reproducibility.

This module provides utilities to initialize and manage random seeds
across numpy, Python's random module, and other libraries to ensure
reproducible results across simulation runs.
"""

import os
import random
import hashlib
from typing import Optional, Union

import numpy as np

from utils.config import DEFAULT_SEED


def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for all relevant libraries to ensure reproducibility.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED from config.

    Returns:
        The seed value that was set.

    Raises:
        ValueError: If the seed is not a valid non-negative integer.
    """
    if seed is None:
        seed = DEFAULT_SEED

    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")

    # Set Python's random module seed
    random.seed(seed)

    # Set NumPy's random seed
    np.random.seed(seed)

    # Set environment variable for other libraries that might respect it
    os.environ['PYTHONHASHSEED'] = str(seed)

    return seed


def get_seed_from_string(seed_str: str) -> int:
    """
    Generate a deterministic seed from a string input using hashing.

    This allows for easy specification of seeds via command-line arguments
    or configuration files while maintaining reproducibility.

    Args:
        seed_str: A string to hash into a seed value.

    Returns:
        A deterministic integer seed value in the range [0, 2^32 - 1].
    """
    if not seed_str:
        raise ValueError("Seed string cannot be empty")

    # Use SHA-256 hash and take the first 32 bits
    hash_obj = hashlib.sha256(seed_str.encode('utf-8'))
    hash_bytes = hash_obj.digest()[:4]
    seed = int.from_bytes(hash_bytes, byteorder='big')

    return seed


def seed_generator(base_seed: int, offset: int = 0) -> int:
    """
    Generate a derived seed from a base seed with an offset.

    Useful for generating multiple independent seeds for parallel
    replications or different components of a simulation.

    Args:
        base_seed: The base seed value.
        offset: An integer offset to generate a unique seed.

    Returns:
        A derived seed value.
    """
    if offset < 0:
        raise ValueError("Offset must be non-negative")

    # Simple linear combination that maintains determinism
    derived_seed = (base_seed + offset * 12345) % (2**32)
    return derived_seed


class SeedManager:
    """
    A context manager for managing random seeds within a specific scope.

    This allows for temporary seed changes that are automatically restored
    to their previous state when exiting the context.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the SeedManager.

        Args:
            seed: The seed to set. If None, uses DEFAULT_SEED.
        """
        self.seed = seed if seed is not None else DEFAULT_SEED
        self._original_python_state = None
        self._original_numpy_state = None

    def __enter__(self) -> 'SeedManager':
        """Save current states and set new seed."""
        # Save current states
        self._original_python_state = random.getstate()
        self._original_numpy_state = np.random.get_state()

        # Set new seed
        set_global_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Restore original states."""
        if self._original_python_state is not None:
            random.setstate(self._original_python_state)
        if self._original_numpy_state is not None:
            np.random.set_state(self._original_numpy_state)


def validate_seed(seed: int) -> bool:
    """
    Validate that a seed value is acceptable.

    Args:
        seed: The seed value to validate.

    Returns:
        True if the seed is valid, False otherwise.
    """
    try:
        if not isinstance(seed, int):
            return False
        if seed < 0:
            return False
        return True
    except Exception:
        return False
