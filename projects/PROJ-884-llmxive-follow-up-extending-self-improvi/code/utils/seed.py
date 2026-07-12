"""
Random seed management utility for reproducibility in llmXive experiments.

This module provides functions to set and retrieve random seeds across
Python's built-in random, NumPy, and PyTorch libraries to ensure
deterministic behavior in experiments.
"""

import random
import os
import hashlib
from typing import Optional, Dict, Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None


# Global seed state to track the current seed
_current_seed: Optional[int] = None


def set_seed(seed: int, deterministic: bool = True) -> Dict[str, Any]:
    """
    Set random seeds for reproducibility across all relevant libraries.

    Args:
        seed (int): The random seed value to use.
        deterministic (bool): If True, sets environment variables for
            deterministic behavior in PyTorch (slower but reproducible).

    Returns:
        dict: A dictionary containing the seed value and status of each library.
    """
    global _current_seed
    _current_seed = seed

    status = {
        "seed": seed,
        "python_random": False,
        "numpy": False,
        "torch": False,
        "torch_deterministic": False
    }

    # Set Python's random seed
    random.seed(seed)
    status["python_random"] = True

    # Set NumPy seed if available
    if HAS_NUMPY and np is not None:
        np.random.seed(seed)
        status["numpy"] = True

    # Set PyTorch seeds if available
    if HAS_TORCH and torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # If deterministic mode is requested
            if deterministic:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
                status["torch_deterministic"] = True
        status["torch"] = True

    return status


def get_seed() -> Optional[int]:
    """
    Retrieve the currently set random seed.

    Returns:
        Optional[int]: The current seed value, or None if not set.
    """
    return _current_seed


def generate_seed_from_string(seed_string: str) -> int:
    """
    Generate a deterministic integer seed from a string input.

    Useful for creating reproducible seeds from experiment names or
    configuration strings.

    Args:
        seed_string (str): The string to convert into a seed.

    Returns:
        int: A 32-bit integer seed derived from the input string.
    """
    hash_obj = hashlib.sha256(seed_string.encode('utf-8'))
    # Take the first 8 hex characters and convert to int
    seed_int = int(hash_obj.hexdigest()[:8], 16)
    return seed_int


def reset_seed() -> None:
    """
    Reset the global seed state to None.
    """
    global _current_seed
    _current_seed = None


def set_deterministic_mode(enabled: bool = True) -> None:
    """
    Enable or disable deterministic mode for PyTorch.

    This sets environment variables and backend flags to ensure
    deterministic behavior in CuDNN operations.

    Args:
        enabled (bool): Whether to enable deterministic mode.
    """
    if HAS_TORCH and torch is not None:
        if enabled:
            os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
            torch.use_deterministic_algorithms(True)
            if torch.cuda.is_available():
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        else:
            torch.use_deterministic_algorithms(False)
            if torch.cuda.is_available():
                torch.backends.cudnn.deterministic = False
                torch.backends.cudnn.benchmark = True

def main():
    """
    CLI entry point for testing seed management.
    """
    import sys

    print("llmXive Seed Management Utility")
    print("-" * 40)

    # Test 1: Generate seed from string
    test_str = "experiment_alpha_001"
    generated_seed = generate_seed_from_string(test_str)
    print(f"Generated seed from '{test_str}': {generated_seed}")

    # Test 2: Set seed and verify
    print(f"\nSetting seed to {generated_seed}...")
    status = set_seed(generated_seed)
    print(f"Status: {status}")

    # Test 3: Verify reproducibility
    if HAS_NUMPY:
        arr1 = np.random.rand(3)
        set_seed(generated_seed)
        arr2 = np.random.rand(3)
        print(f"\nReproducibility check (NumPy):")
        print(f"Array 1: {arr1}")
        print(f"Array 2: {arr2}")
        print(f"Arrays match: {np.allclose(arr1, arr2)}")

    if HAS_TORCH:
        tensor1 = torch.rand(3)
        set_seed(generated_seed)
        tensor2 = torch.rand(3)
        print(f"\nReproducibility check (PyTorch):")
        print(f"Tensor 1: {tensor1}")
        print(f"Tensor 2: {tensor2}")
        print(f"Tensors match: {torch.allclose(tensor1, tensor2)}")

    print("\nSeed management utility test complete.")

if __name__ == "__main__":
    main()