"""
Global seed setting utility for reproducible experiments.

This module provides a centralized function to set random seeds for:
- Python's built-in random module
- NumPy
- PyTorch (including CUDA determinism if available)

All seeds are set to the same integer value to ensure reproducibility
across the entire pipeline.
"""

import random
import os
from typing import Optional

import numpy as np
import torch


def set_global_seed(seed: int, deterministic: bool = True) -> None:
    """
    Set global random seeds for reproducibility across the pipeline.

    Args:
        seed: The integer seed value to use.
        deterministic: If True, set torch.backends.cudnn.deterministic and
                       torch.backends.cudnn.benchmark to ensure deterministic
                       behavior (may impact performance).

    Raises:
        ValueError: If seed is not a non-negative integer.
    """
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")

    # Set Python random seed
    random.seed(seed)

    # Set NumPy seed
    np.random.seed(seed)

    # Set PyTorch seeds (CPU and GPU)
    torch.manual_seed(seed)

    # Set CUDA seeds if available
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    # Set deterministic behavior if requested
    if deterministic and torch.backends.cudnn.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Set environment variable for deterministic operations
    os.environ['PYTHONHASHSEED'] = str(seed)
    os.environ['TF_DETERMINISTIC_OPS'] = '1'  # For TensorFlow if used later

def get_seed_environment_variable() -> Optional[int]:
    """
    Retrieve the seed from the environment variable if set.

    Returns:
        The seed value as an integer if set, None otherwise.
    """
    seed_str = os.environ.get('PYTHONHASHSEED')
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            return None
    return None

def set_seed_from_environment() -> None:
    """
    Set global seeds using the value from the PYTHONHASHSEED environment variable.

    If the environment variable is not set, uses a default seed of 42.
    """
    seed = get_seed_environment_variable()
    if seed is None:
        seed = 42  # Default seed
    set_global_seed(seed)
