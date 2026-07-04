"""
Utility functions for deterministic random seed management.

This module ensures reproducibility across Python's random module and NumPy
by setting seeds at the start of execution. It is designed to be called
early in the pipeline (e.g., from the CLI entry point) before any
stochastic operations occur.
"""

import random
import os
from typing import Optional

import numpy as np


def set_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility across the entire pipeline.

    This function ensures that:
    1. Python's built-in `random` module is seeded.
    2. NumPy's random number generator is seeded.
    3. The `PYTHONHASHSEED` environment variable is set (if not already set)
       to ensure dictionary and set iteration order is deterministic.

    Args:
        seed (int): The integer seed value to use. Must be non-negative.
    """
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy's random seed
    np.random.seed(seed)

    # Set PYTHONHASHSEED for deterministic hash-based data structures
    # This is critical for reproducibility in dictionaries and sets
    if "PYTHONHASHSEED" not in os.environ:
        os.environ["PYTHONHASHSEED"] = str(seed)