"""
Seed fixing utility for reproducibility across all scripts.

This module provides functions to set random seeds for Python's built-in random
module, NumPy, and PyTorch (including CUDA operations) to ensure reproducible
results across runs.
"""

import os
import random
from typing import Optional

import numpy as np
import torch


def set_seed(seed: int = 42, deterministic: bool = True) -> None:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.

    Args:
        seed: The random seed value to use (default: 42).
        deterministic: If True, sets CuDNN to deterministic mode. Note that
            this may impact performance and is only available when using CUDA.
    """
    # Set environment variable for PyTorch
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Python random module
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch CPU and GPU
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # if multi-GPU

    # PyTorch deterministic behavior
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Record the seed for logging
    print(f"Random seed set to: {seed}")


def get_seed_value(seed: Optional[int] = None) -> int:
    """
    Get the current seed value, using a default if none provided.

    Args:
        seed: Optional seed value. If None, returns the default (42).

    Returns:
        The seed value to use.
    """
    return seed if seed is not None else 42