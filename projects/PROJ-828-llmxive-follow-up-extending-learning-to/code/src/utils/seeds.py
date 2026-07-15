"""
Deterministic seed pinning utilities for reproducible experiments.

This module ensures that all random number generators (Python, NumPy, PyTorch)
are seeded consistently across different training variants to guarantee
reproducible results.
"""

import os
import random
import hashlib
from typing import Optional, Dict, Any

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


def set_seed(seed: int, deterministic: bool = True) -> Dict[str, Any]:
    """
    Set seeds for all random number generators to ensure reproducibility.

    Args:
        seed (int): The random seed to use.
        deterministic (bool): If True, enforce deterministic behavior in CuDNN
                              (only relevant if GPU is available, but we set it anyway).

    Returns:
        Dict[str, Any]: A dictionary containing the seed value and status of each library.
    """
    results = {
        "seed": seed,
        "python": False,
        "numpy": False,
        "torch": False,
        "deterministic_mode": False
    }

    # Set Python random seed
    random.seed(seed)
    results["python"] = True

    # Set NumPy seed
    if HAS_NUMPY:
        np.random.seed(seed)
        results["numpy"] = True

    # Set PyTorch seeds
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure CuDNN is deterministic
            if deterministic:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
            results["deterministic_mode"] = deterministic
        results["torch"] = True

    # Set environment variable for reproducibility
    os.environ["PYTHONHASHSEED"] = str(seed)

    return results


def generate_seed_from_string(seed_string: str, offset: int = 0) -> int:
    """
    Generate a deterministic integer seed from a string input.

    This is useful for generating unique but reproducible seeds for
    different experiment variants based on their configuration names.

    Args:
        seed_string (str): The string to hash.
        offset (int): An integer offset to add to the generated seed.

    Returns:
        int: A deterministic integer seed.
    """
    hash_obj = hashlib.sha256(seed_string.encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)
    return (hash_int + offset) % (2**32 - 1)


def get_seed_config(seed: int) -> Dict[str, Any]:
    """
    Create a comprehensive seed configuration dictionary.

    Args:
        seed (int): The base seed.

    Returns:
        Dict[str, Any]: Configuration dictionary with seed and related settings.
    """
    return {
        "base_seed": seed,
        "deterministic": True,
        "torch_deterministic": True,
        "torch_cudnn_benchmark": False
    }


def apply_seed_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply a seed configuration dictionary to the environment.

    Args:
        config (Dict[str, Any]): Configuration dictionary from get_seed_config.

    Returns:
        Dict[str, Any]: Results from set_seed with the applied seed.
    """
    seed = config.get("base_seed", 42)
    deterministic = config.get("deterministic", True)
    return set_seed(seed, deterministic)
