"""
Utility module for managing random seeds across numpy, random, and torch (if available).
Ensures reproducibility of experiments.
"""
import random
import os
from typing import Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


_global_seed: Optional[int] = None


def set_global_seed(seed: int = 42) -> None:
    """
    Set the global random seed for reproducibility across libraries.

    Args:
        seed: Integer seed value.
    """
    global _global_seed
    _global_seed = seed

    # Python random
    random.seed(seed)

    # NumPy
    if HAS_NUMPY:
        np.random.seed(seed)

    # PyTorch
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior where possible
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Environment variable for some libraries
    os.environ["PYTHONHASHSEED"] = str(seed)


def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.

    Returns:
        The integer seed if set, None otherwise.
    """
    return _global_seed
