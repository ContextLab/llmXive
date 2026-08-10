"""
code/utils/seeds.py

Manages random seeds for all sampling and statistical resampling operations
to ensure reproducibility across the research pipeline.
"""

import random
import numpy as np
import os
from typing import Optional


# Default seed value for reproducibility
DEFAULT_SEED = 42


def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Sets the random seed for the entire pipeline to ensure reproducibility.

    This function configures seeds for:
    - Python's built-in random module
    - NumPy's random number generator
    - The environment variable PYTHONHASHSEED (for hash randomization control)

    Args:
        seed (Optional[int]): The seed value to use. If None, uses DEFAULT_SEED.

    Returns:
        int: The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set seed for Python's random module
    random.seed(seed)

    # Set seed for NumPy
    np.random.seed(seed)

    # Set environment variable for hash randomization (affects dict/set ordering)
    os.environ['PYTHONHASHSEED'] = str(seed)

    return seed


def get_seed_manager(seed: Optional[int] = None):
    """
    Context manager / factory for creating isolated random states for specific tasks.

    Useful when a specific part of the pipeline needs a distinct but reproducible
    random sequence without affecting the global state.

    Args:
        seed (Optional[int]): Base seed. If None, uses DEFAULT_SEED.

    Returns:
        A function that generates a new random.Random instance and np.random.Generator
        derived from the provided seed.
    """
    base_seed = seed if seed is not None else DEFAULT_SEED

    def create_rng(offset: int = 0):
        """
        Creates a new random state with a derived seed to ensure independence.

        Args:
            offset (int): An integer offset to derive a unique seed for this instance.

        Returns:
            tuple: (random.Random instance, np.random.Generator instance)
        """
        derived_seed = base_seed + offset
        rng_python = random.Random(derived_seed)
        rng_numpy = np.random.default_rng(derived_seed)
        return rng_python, rng_numpy

    return create_rng


# Convenience function for sampling with a specific seed
def sample_with_seed(data, n: int, seed: Optional[int] = None, replace: bool = False):
    """
    Samples n items from data using a reproducible seed.

    Args:
        data (list or np.ndarray): The data to sample from.
        n (int): Number of items to sample.
        seed (Optional[int]): Seed for reproducibility.
        replace (bool): Whether to sample with replacement.

    Returns:
        list: The sampled items.
    """
    if seed is not None:
        set_global_seed(seed)
    
    if isinstance(data, np.ndarray):
        return list(np.random.choice(data, size=n, replace=replace))
    else:
        return random.sample(data, n) if not replace else random.choices(data, k=n)