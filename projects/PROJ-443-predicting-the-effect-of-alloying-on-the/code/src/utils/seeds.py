"""
Seed management module for reproducible experiments.

This module provides utilities to set and retrieve random seeds across
Python's random, NumPy, and other common ML libraries to ensure
reproducibility of experiments.
"""

import os
import random
from typing import Optional

import numpy as np

# Global seed storage
_global_seed: Optional[int] = None


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across all libraries.

    Args:
        seed: The random seed to use. Defaults to 42.
    """
    global _global_seed
    _global_seed = seed

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy's random seed
    np.random.seed(seed)

    # Set environment variable for frameworks that check it
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Try to set torch seed if available (CPU-only constraint)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass  # PyTorch not installed, skip

    # Try to set tensorflow seed if available
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass  # TensorFlow not installed, skip

    # Try to set sklearn seed (uses random_state parameter in estimators)
    try:
        import sklearn
        # sklearn doesn't have a global seed, but we ensure numpy is seeded
    except ImportError:
        pass


def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.

    Returns:
        The global seed if set, None otherwise.
    """
    return _global_seed


class SeedContext:
    """
    Context manager for temporary seed setting.

    Allows setting a seed for a specific block of code and restoring
    the previous seed state afterward.

    Example:
        with SeedContext(123):
            # Code here uses seed 123
            pass
        # Seed restored to previous value
    """

    def __init__(self, seed: int):
        """
        Initialize the context with a specific seed.

        Args:
            seed: The seed to use within the context.
        """
        self.seed = seed
        self.previous_seed = None

    def __enter__(self):
        """Enter the context and set the seed."""
        self.previous_seed = _global_seed
        set_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore the previous seed."""
        global _global_seed
        _global_seed = self.previous_seed


def get_random_state() -> np.random.RandomState:
    """
    Get a new RandomState instance initialized with the global seed.

    Returns:
        A numpy RandomState instance.
    """
    seed = _global_seed if _global_seed is not None else 42
    return np.random.RandomState(seed)