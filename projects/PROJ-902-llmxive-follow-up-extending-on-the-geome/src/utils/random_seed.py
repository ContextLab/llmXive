"""
Deterministic RNG helper for reproducible experiments.

This module provides a unified function to seed Python's built-in `random`,
`numpy`, and `torch` (if available) to ensure deterministic behavior across
runs. It is designed to be called at the very beginning of any experimental
script to guarantee reproducibility.
"""

import random
import os
import hashlib
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


def set_seed(seed: int, deterministic: bool = True) -> None:
    """
    Set the random seed for Python, NumPy, and PyTorch to ensure reproducibility.

    Args:
        seed (int): The integer seed value.
        deterministic (bool): If True, forces deterministic algorithms in PyTorch
            (e.g., CuDNN) and sets environment variables for reproducibility.
            Note: This may impact performance and is not always compatible with
            all operations (e.g., certain atomic reductions).
    """
    # 1. Set Python's random seed
    random.seed(seed)

    # 2. Set NumPy seed
    if HAS_NUMPY:
        np.random.seed(seed)

    # 3. Set PyTorch seeds and configuration
    if HAS_TORCH:
        torch.manual_seed(seed)
        # Set seed for GPU operations if available
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)

        if deterministic:
            # Force deterministic behavior in CuDNN
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

            # Set environment variable for deterministic operations
            # This is required for some operations to be deterministic
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
            os.environ["PYTHONHASHSEED"] = str(seed)

            # In PyTorch >= 1.8, use this to enforce deterministic algorithms
            try:
                torch.use_deterministic_algorithms(True)
            except AttributeError:
                # Fallback for older versions if necessary, though use_deterministic_algorithms is standard now
                pass

def generate_seed_from_string(seed_string: str) -> int:
    """
    Generate a deterministic integer seed from a string input.

    This is useful for deriving seeds from experiment names or configuration
    keys while maintaining reproducibility.

    Args:
        seed_string (str): The input string to hash.

    Returns:
        int: A 32-bit integer seed derived from the hash of the string.
    """
    # Use SHA-256 for robust hashing, then take the first 4 bytes as an integer
    hash_obj = hashlib.sha256(seed_string.encode("utf-8"))
    hash_bytes = hash_obj.digest()[:4]
    return int.from_bytes(hash_bytes, byteorder="big")

def get_seed_info() -> dict:
    """
    Returns a dictionary describing the current state of RNG libraries.

    Returns:
        dict: A dictionary with keys 'python', 'numpy', 'torch' indicating
              whether the library is available and its current seed state
              (if retrievable, otherwise None).
    """
    info = {
        "python": random.getstate()[1][0] if random.getstate() else None,
        "numpy": None,
        "torch": None,
        "available_libraries": []
    }

    if HAS_NUMPY:
        info["available_libraries"].append("numpy")
        info["numpy"] = np.random.get_state()[1][0]

    if HAS_TORCH:
        info["available_libraries"].append("torch")
        # Getting the exact seed state of torch is not directly exposed as a single int
        # in the same way as random, but we can note availability.
        info["torch"] = "seeded" if torch.initial_seed() is not None else "unseeded"

    return info