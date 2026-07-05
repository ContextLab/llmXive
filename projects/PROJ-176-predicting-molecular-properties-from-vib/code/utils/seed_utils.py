"""
seed_utils.py

Provides utilities to pin random seeds for reproducibility across
Python, NumPy, and PyTorch, adhering to Principle I of the research protocol.
"""

import os
import random
import numpy as np
import torch

# Attempt to import CUDA-specific functionality only if available
try:
    from torch.backends import cudnn
    CUDA_AVAILABLE = True
except ImportError:
    CUDA_AVAILABLE = False


def set_seed(seed: int = 42) -> None:
    """
    Sets the random seed for all relevant libraries to ensure reproducibility.

    Args:
        seed (int): The integer seed value. Default is 42.
    """
    # Set Python built-in random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set PyTorch random seed
    torch.manual_seed(seed)

    # Set PyTorch CUDA random seed if available
    if CUDA_AVAILABLE and torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # If using multi-GPU

        # Deterministic behavior settings for CUDA
        # Note: These may impact performance but ensure reproducibility
        cudnn.deterministic = True
        cudnn.benchmark = False

    # Set environment variable for deterministic operations in PyTorch
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_seed_info(seed: int = 42) -> dict:
    """
    Returns a dictionary containing the current seed configuration status.

    Args:
        seed (int): The seed value being used.

    Returns:
        dict: A dictionary with status of seed setting for each library.
    """
    return {
        "seed": seed,
        "python_random": random.getstate()[1][0],
        "numpy": np.random.get_state()[1][0],
        "torch": torch.initial_seed(),
        "cuda_available": CUDA_AVAILABLE and torch.cuda.is_available(),
        "cudnn_deterministic": cudnn.deterministic if CUDA_AVAILABLE else False,
        "cudnn_benchmark": cudnn.benchmark if CUDA_AVAILABLE else False
    }
