"""
Seed pinning utility for reproducible experiments (Reproducibility Principle I).

This module provides functions to set and verify random seeds across
Python's random, NumPy, and other relevant libraries to ensure
reproducible results in machine learning experiments.
"""

import os
import random
import hashlib
from typing import Optional, Dict, Any, List
import numpy as np
from .logging import log_info, log_warning, log_error

# Default seed for experiments
DEFAULT_SEED = 42


def get_default_seed() -> int:
    """Return the default seed value used across experiments."""
    return DEFAULT_SEED


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for reproducibility across all relevant libraries.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set seed for Python's random module
    random.seed(seed)

    # Set seed for NumPy
    np.random.seed(seed)

    # Set environment variable for TensorFlow/PyTorch if available
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Log the seed setting
    log_info(f"Random seed set to: {seed}")

    return seed


def get_seed_hash(seed: int) -> str:
    """
    Generate a hash representation of a seed for experiment identification.

    Args:
        seed: The seed value to hash.

    Returns:
        A hexadecimal hash string of the seed.
    """
    return hashlib.sha256(str(seed).encode()).hexdigest()[:16]


def verify_seed_consistency(seeds: List[int], expected_seed: int) -> bool:
    """
    Verify that all provided seeds match the expected seed.

    Args:
        seeds: List of seed values to check.
        expected_seed: The expected seed value.

    Returns:
        True if all seeds match the expected seed, False otherwise.
    """
    if not seeds:
        log_warning("No seeds provided for verification")
        return False

    all_match = all(seed == expected_seed for seed in seeds)

    if not all_match:
        log_warning(f"Seed inconsistency detected. Expected {expected_seed}, got {seeds}")

    return all_match


class SeedContext:
    """
    Context manager for temporary seed setting with automatic restoration.

    Usage:
        with SeedContext(123):
            # Code that needs specific seed
            pass
        # Seed restored to original value
    """

    def __init__(self, seed: int):
        """
        Initialize the seed context.

        Args:
            seed: The seed value to use within the context.
        """
        self.seed = seed
        self.original_random_state = random.getstate()
        self.original_numpy_state = np.random.get_state()
        self.original_hash_seed = os.environ.get('PYTHONHASHSEED')

    def __enter__(self):
        """Set the seed when entering the context."""
        set_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore the original seed state when exiting the context."""
        random.setstate(self.original_random_state)
        np.random.set_state(self.original_numpy_state)
        if self.original_hash_seed is not None:
            os.environ['PYTHONHASHSEED'] = self.original_hash_seed
        elif 'PYTHONHASHSEED' in os.environ:
            del os.environ['PYTHONHASHSEED']

        log_info("Seed context exited, original state restored")
        return False


def generate_experiment_id(seed: Optional[int] = None, prefix: str = "exp") -> str:
    """
    Generate a unique experiment ID based on the seed and timestamp.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.
        prefix: Prefix for the experiment ID.

    Returns:
        A unique experiment ID string.
    """
    if seed is None:
        seed = DEFAULT_SEED

    seed_hash = get_seed_hash(seed)
    timestamp = os.urandom(8).hex()

    return f"{prefix}_{seed_hash}_{timestamp}"


def get_environment_seeds() -> Dict[str, Any]:
    """
    Get the current state of all random number generator seeds.

    Returns:
        Dictionary containing current seed states for various libraries.
    """
    return {
        'python_random': random.getstate()[1][0],
        'numpy_random': np.random.get_state()[1][0],
        'python_hash_seed': os.environ.get('PYTHONHASHSEED', 'not_set'),
    }
