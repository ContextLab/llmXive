"""
Seed Manager Module.

Enforces fixed random seeds for reproducibility across all major
numerical libraries (numpy, python random, torch, tensorflow, etc.)
to satisfy PRINCIPLE I: Reproducibility.

Usage:
    from utils.seed_manager import set_global_seed
    set_global_seed(42)
"""
import os
import random
import sys
from typing import Optional

import numpy as np

# Optional imports for deep learning frameworks (fail gracefully if not installed)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

try:
    import cudnn
    # Only needed if using specific cuDNN determinism settings, handled in torch block usually
except ImportError:
    pass

_GLOBAL_SEED: Optional[int] = None


def set_global_seed(seed: int) -> None:
    """
    Set the random seed for Python, NumPy, and optional deep learning frameworks.

    This function ensures deterministic behavior across the entire pipeline
    by seeding all relevant randomness sources.

    Args:
        seed (int): The integer seed value to use. Must be non-negative.

    Raises:
        ValueError: If seed is negative.
    """
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")

    global _GLOBAL_SEED
    _GLOBAL_SEED = seed

    # 1. Python Standard Library
    random.seed(seed)

    # 2. NumPy
    np.random.seed(seed)

    # 3. PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Enable deterministic behavior in cuDNN
            # Note: This may impact performance
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # 4. TensorFlow (if available)
    if TF_AVAILABLE:
        tf.random.set_seed(seed)
        # Ensure deterministic operations where possible
        os.environ['TF_DETERMINISTIC_OPS'] = '1'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    # 5. Environment variables for reproducibility
    # Some libraries respect these environment variables
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> Optional[int]:
    """
    Retrieve the currently set global seed.

    Returns:
        Optional[int]: The global seed if set, None otherwise.
    """
    return _GLOBAL_SEED
