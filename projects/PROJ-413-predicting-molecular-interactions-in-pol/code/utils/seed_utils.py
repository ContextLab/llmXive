"""
Seed fixing utility for reproducibility across all scripts.

This module provides functions to set random seeds for Python's built-in random
module, NumPy, and PyTorch (including CUDA operations) to ensure reproducible
results across runs.
"""

import os
import random
import platform
from typing import Optional

import numpy as np
import torch


def set_seed(seed: int = 42, deterministic: bool = True) -> None:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.

    This function sets seeds for:
    - Python's built-in random module
    - NumPy
    - PyTorch (CPU and GPU)
    - Python hash randomization (via environment variable)

    Args:
        seed: The random seed value to use (default: 42).
        deterministic: If True, sets CuDNN to deterministic mode. Note that
            this may impact performance and is only available when using CUDA.
            On CPU-only systems, this flag is ignored for CuDNN settings but
            other deterministic behaviors are still applied.
    """
    # Set environment variable for Python hash randomization
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Python random module
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch CPU and GPU
    torch.manual_seed(seed)
    
    # Check if CUDA is available
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # if multi-GPU
    else:
        # On CPU-only systems (common in CI runners), skip CUDA seed setting
        # but log that we are running in CPU-only mode
        pass

    # PyTorch deterministic behavior
    if deterministic:
        # Only set CuDNN flags if CUDA is available
        if torch.cuda.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        else:
            # On CPU-only systems, we can still set some deterministic flags
            # but CuDNN flags are not applicable
            pass

    # Record the seed for logging
    system_type = "GPU" if torch.cuda.is_available() else "CPU"
    print(f"Random seed set to: {seed} ({system_type} mode)")


def get_seed_value(seed: Optional[int] = None) -> int:
    """
    Get the current seed value, using a default if none provided.

    Args:
        seed: Optional seed value. If None, returns the default (42).

    Returns:
        The seed value to use.
    """
    return seed if seed is not None else 42