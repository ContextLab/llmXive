"""
Deterministic random seed management for reproducible experiments.

This module provides functions to set and reset random seeds across
Python's random module, NumPy, and PyTorch to ensure deterministic
behavior in research experiments.
"""

import random
import os
import torch
import numpy as np
from typing import Optional

# Default seed value for reproducibility
DEFAULT_SEED = 42

# Store the current seed environment for potential reset
_current_seed_env: Optional[int] = None


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.

    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set.

    Side Effects:
        - Sets PYTHONHASHSEED environment variable
        - Seeds random.random
        - Seeds numpy.random
        - Seeds torch.manual_seed, torch.cuda.manual_seed, etc.
        - Sets CuDNN deterministic behavior flags if CUDA is available
    """
    global _current_seed_env

    if seed is None:
        seed = DEFAULT_SEED

    _current_seed_env = seed

    # Set Python random seed
    random.seed(seed)

    # Set NumPy seed
    np.random.seed(seed)

    # Set PyTorch seeds
    torch.manual_seed(seed)

    # If CUDA is available, set additional CUDA seeds
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # If using multi-GPU
        # Ensure deterministic behavior in CuDNN
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Set environment variable for hash randomization (affects dict ordering in some Python versions)
    os.environ['PYTHONHASHSEED'] = str(seed)

    return seed


def get_seed_env() -> Optional[int]:
    """
    Retrieve the currently active seed value.

    Returns:
        The seed value set by the last call to set_seed(), or None if
        set_seed() has not been called yet.
    """
    return _current_seed_env


def reset_seeds_to_default() -> int:
    """
    Reset all random seeds to the default value.

    Returns:
        The default seed value (42).
    """
    return set_seed(DEFAULT_SEED)