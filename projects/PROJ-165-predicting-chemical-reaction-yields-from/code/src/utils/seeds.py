"""
Deterministic random seed management for reproducible experiments.

This module provides utilities to set and manage random seeds across
Python's random, NumPy, and PyTorch libraries to ensure reproducible
results.
"""

import random
import os
import torch
import numpy as np
from typing import Optional


# Default seed value used if none is provided
DEFAULT_SEED = 42


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for Python, NumPy, and PyTorch to ensure reproducibility.

    Args:
        seed (int, optional): The seed value to use. If None, uses DEFAULT_SEED.

    Returns:
        int: The seed value that was set.

    Notes:
        - Sets PYTHONHASHSEED environment variable if not already set.
        - Sets torch.manual_seed, torch.cuda.manual_seed, torch.cuda.manual_seed_all.
        - Sets numpy.random.seed and random.seed.
        - Sets deterministic cuDNN behavior if CUDA is available.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set environment variable for hash randomization
    os.environ["PYTHONHASHSEED"] = str(seed)

    # Python's random module
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch
    torch.manual_seed(seed)

    # If CUDA is available, set seeds for CUDA operations
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior for CUDA operations
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # For reproducibility in DataLoader workers
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

    return seed


def get_seed_env() -> Optional[int]:
    """
    Retrieve the seed value from the environment variable if set.

    Returns:
        int or None: The seed value from PYTHONHASHSEED environment variable,
                     or None if not set.
    """
    seed_str = os.environ.get("PYTHONHASHSEED")
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            return None
    return None


def reset_seeds_to_default() -> int:
    """
    Reset all random seeds to the default value.

    Returns:
        int: The default seed value that was set.
    """
    return set_seed(DEFAULT_SEED)
