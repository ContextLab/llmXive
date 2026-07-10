"""
Utilities for setting global random seeds to ensure reproducibility across
numpy, random, torch, and tensorflow.

This module addresses the requirement for deterministic execution in scientific
pipelines, ensuring that stochastic processes (e.g., initialization, sampling)
yield identical results across runs when the seed is fixed.
"""
import os
import random
import hashlib
from typing import Optional

try:
    import numpy as np
except ImportError:
    np = None

try:
    import torch
except ImportError:
    torch = None

try:
    import tensorflow as tf
except ImportError:
    tf = None


def set_seed(seed: int = 42) -> None:
    """
    Set global random seeds for all relevant libraries to ensure reproducibility.

    Args:
        seed (int): The seed value to use. Defaults to 42.
    """
    # Set Python's built-in random module
    random.seed(seed)

    # Set numpy seed
    if np is not None:
        np.random.seed(seed)

    # Set torch seed if available
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CUDA operations if possible
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # Set tensorflow seed if available
    if tf is not None:
        tf.random.set_seed(seed)

    # Set environment variables for parallelism control (optional but recommended)
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_seed_hash(seed: int, prefix: str = "seed") -> str:
    """
    Generate a deterministic hash string from a seed value for use in file naming
    or logging to uniquely identify a run configuration.

    Args:
        seed (int): The seed value.
        prefix (str): A prefix for the hash string.

    Returns:
        str: A hexadecimal hash string.
    """
    input_str = f"{prefix}_{seed}"
    return hashlib.sha256(input_str.encode()).hexdigest()[:16]


def reset_seeds_to_default() -> None:
    """
    Reset all seeds to the default value (42).
    """
    set_seed(42)
