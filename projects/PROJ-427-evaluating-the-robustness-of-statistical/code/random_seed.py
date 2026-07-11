"""
Random seed management for reproducible experiments.

This module provides a centralized way to set deterministic seeds
for all random number generators used in the project.
"""
import random
import os
import numpy as np

# Optional: Set PyTorch seed if available (common in ML/stats pipelines)
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


def set_seed(seed: int = 42) -> None:
    """
    Set the random seed for all relevant libraries to ensure reproducibility.

    Args:
        seed (int): The integer seed value. Default is 42.
    """
    # Set Python's built-in random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set environment variable for some C-level libraries (e.g., OpenMP)
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Set PyTorch seeds if available
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CUDA operations
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
