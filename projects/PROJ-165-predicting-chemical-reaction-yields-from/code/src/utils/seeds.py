"""
Deterministic random seed management for reproducible experiments.

This module provides utilities to set and manage random seeds across
Python's random module, NumPy, and PyTorch to ensure reproducibility
of experiments.
"""

import random
import os
import torch
import numpy as np
from typing import Optional


# Default seed value used when no specific seed is provided
DEFAULT_SEED = 42


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.

    Args:
        seed: The random seed to set. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set.

    This function sets seeds for:
        - Python's random module
        - NumPy (including random number generation)
        - PyTorch (CPU and CUDA)
        - Environment variables for deterministic behavior

    Note:
        When using CUDA, some operations may still be non-deterministic.
        For full determinism in CUDA, see torch.use_deterministic_algorithms(True)
        and setting CUBLAS_WORKSPACE_CONFIG environment variable.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set Python random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set PyTorch random seeds
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # If using multi-GPU

    # Set environment variables for deterministic behavior
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Configure PyTorch for deterministic behavior
    torch.use_deterministic_algorithms(True, warn_only=True)

    # For CUDA determinism (if available)
    if torch.cuda.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    return seed


def get_seed_env() -> Optional[int]:
    """
    Retrieve the seed value from the environment variable or return None.

    Returns:
        The seed value from the PYTHONHASHSEED environment variable if set,
        otherwise None.
    """
    seed_str = os.environ.get('PYTHONHASHSEED')
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
        The default seed value that was set.

    This is a convenience function that calls set_seed with DEFAULT_SEED.
    """
    return set_seed(DEFAULT_SEED)