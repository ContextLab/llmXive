"""
Seed management utility for llmXive project.

This module provides a centralized way to pin all random states across
the entire project to ensure reproducibility of experiments.
"""

import random
import os
from typing import Optional, List

# Try to import numpy if available (common in this project's stack)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Try to import torch if available
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Try to import tensorflow if available
try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

# Try to import sklearn if available
try:
    import sklearn
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Default seed value for the project
DEFAULT_SEED = 42


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for all supported libraries to ensure reproducibility.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED (42).

    Returns:
        The seed value that was set.

    Note:
        This function sets seeds for:
        - Python's random module
        - NumPy (if installed)
        - PyTorch (if installed)
        - TensorFlow (if installed)
        - scikit-learn (via numpy seed)

        It also sets the PYTHONHASHSEED environment variable for
        deterministic behavior in hashing.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Ensure seed is an integer
    seed = int(seed)

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy seed
    if HAS_NUMPY:
        np.random.seed(seed)

    # Set PyTorch seeds
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # Set TensorFlow seeds
    if HAS_TENSORFLOW:
        tf.random.set_seed(seed)

    # Set environment variable for hash seed
    os.environ['PYTHONHASHSEED'] = str(seed)

    return seed


def get_random_state(seed: Optional[int] = None):
    """
    Get a random state object for reproducible random number generation.

    This is useful when you need to pass a random state to a function
    that requires it, rather than setting a global seed.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED (42).

    Returns:
        A random.Random instance (or np.random.RandomState if numpy is available
        and requested).
    """
    if seed is None:
        seed = DEFAULT_SEED

    if HAS_NUMPY:
        return np.random.RandomState(seed)
    else:
        return random.Random(seed)


def set_all_seeds(seed: Optional[int] = None) -> int:
    """
    Alias for set_seed to provide a more explicit name.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED (42).

    Returns:
        The seed value that was set.
    """
    return set_seed(seed)


def get_seed() -> int:
    """
    Get the current default seed value.

    Returns:
        The current default seed value.
    """
    return DEFAULT_SEED


def set_seed_from_env(seed_env_var: str = "SEED", default: Optional[int] = None) -> int:
    """
    Set seed from an environment variable, falling back to a default.

    Args:
        seed_env_var: The name of the environment variable to read.
        default: The default seed value if the env var is not set.
                 If None, uses DEFAULT_SEED (42).

    Returns:
        The seed value that was set.
    """
    seed_str = os.environ.get(seed_env_var)
    if seed_str is not None:
        try:
            seed = int(seed_str)
        except ValueError:
            raise ValueError(f"Invalid seed value in environment variable '{seed_env_var}': {seed_str}")
    else:
        seed = default if default is not None else DEFAULT_SEED

    return set_seed(seed)