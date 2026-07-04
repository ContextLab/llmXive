"""
Seeding utilities for reproducible research.

This module ensures deterministic behavior across numpy, random, and torch
by pinning random seeds to a fixed value (42). It also provides verification
utilities to confirm that outputs are deterministic upon re-runs.
"""

import random
import os
from typing import Optional

# Attempt to import numpy and torch; handle cases where they are not installed
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

# Default seed value as per task requirements
DEFAULT_SEED = 42


def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Pin random seeds for numpy, random, and torch to ensure reproducibility.

    Args:
        seed (int): The seed value to use. Defaults to 42.
    """
    # Set seed for the built-in random module
    random.seed(seed)

    # Set seed for numpy if available
    if HAS_NUMPY:
        np.random.seed(seed)
        # Ensure deterministic behavior in numpy operations where possible
        # Note: np.random.seed is deprecated in favor of Generator, but maintained for compatibility
        # with older codebases. For new code, consider using np.random.default_rng(seed).

    # Set seeds for torch if available
    if HAS_TORCH:
        torch.manual_seed(seed)
        # Set seeds for CUDA if available
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # If using multi-GPU
            # Ensure deterministic behavior in CUDA operations
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

        # Set environment variable for deterministic CuDNN behavior
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        os.environ['PYTHONHASHSEED'] = str(seed)


def verify_determinism(seed: int = DEFAULT_SEED, runs: int = 2) -> bool:
    """
    Verify that setting the seed produces deterministic outputs.

    This function runs a simple random operation twice and compares the results.
    If the results are identical, the seed pinning is considered successful.

    Args:
        seed (int): The seed value to test. Defaults to 42.
        runs (int): Number of times to run the verification. Defaults to 2.

    Returns:
        bool: True if all runs produce identical results, False otherwise.
    """
    if runs < 2:
        raise ValueError("Number of runs must be at least 2 for verification.")

    results = []

    for i in range(runs):
        set_seed(seed)
        current_result = {}

        # Test random module
        current_result['random'] = [random.random() for _ in range(5)]

        # Test numpy if available
        if HAS_NUMPY:
            current_result['numpy'] = np.random.rand(5).tolist()

        # Test torch if available
        if HAS_TORCH:
            current_result['torch'] = torch.rand(5).tolist()

        results.append(current_result)

    # Compare results from all runs
    first_result = results[0]
    for i in range(1, runs):
        if results[i] != first_result:
            return False

    return True


def main() -> None:
    """
    Main entry point to demonstrate seed pinning and verification.
    """
    print(f"Setting seed to {DEFAULT_SEED}...")
    set_seed(DEFAULT_SEED)

    # Demonstrate that seeds are set
    print("\nDemonstrating random outputs after setting seed:")
    print(f"  random.random(): {random.random()}")
    if HAS_NUMPY:
        print(f"  np.random.rand(): {np.random.rand()}")
    if HAS_TORCH:
        print(f"  torch.rand(): {torch.rand()}")

    # Verify determinism
    print(f"\nVerifying determinism with {DEFAULT_SEED}...")
    is_deterministic = verify_determinism(DEFAULT_SEED)
    if is_deterministic:
        print("  SUCCESS: Outputs are deterministic across runs.")
    else:
        print("  FAILURE: Outputs are NOT deterministic across runs.")


if __name__ == "__main__":
    main()