"""
Seed configuration and fixation enforcement for llmXive pipeline.

This module implements Constitution Principle I (Reproducibility) and FR-005
by providing a centralized mechanism to set and enforce random seeds across
all random number generators used in the pipeline (numpy, random, torch).
"""

import os
import random
import numpy as np
from typing import Optional

# Default seed for reproducibility
DEFAULT_SEED = 42
SEED_ENV_VAR = "LLMXIVE_SEED"

def get_seed() -> int:
    """Retrieve the seed value from environment variable or use default."""
    seed_str = os.environ.get(SEED_ENV_VAR)
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            raise ValueError(f"Invalid seed value in {SEED_ENV_VAR}: '{seed_str}'. Must be an integer.")
    return DEFAULT_SEED

def set_seeds(seed: Optional[int] = None) -> int:
    """Set seeds for all random number generators to ensure reproducibility."""
    if seed is None:
        seed = get_seed()

    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")

    np.random.seed(seed)
    random.seed(seed)

    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass

    try:
        import pybullet as p
        os.environ["PYBULLET_ENABLE_DETERMINISTIC"] = "1"
    except ImportError:
        pass

    return seed

def init_reproducibility() -> int:
    """Initialize reproducibility for the current run."""
    return set_seeds()

if __name__ == "__main__":
    seed_val = init_reproducibility()
    print(f"Seeds set to: {seed_val}")
    # Simple determinism check
    a = np.random.rand(5)
    init_reproducibility()
    b = np.random.rand(5)
    assert np.allclose(a, b), "Numpy seed not deterministic!"
    print("SUCCESS: Seed fixation verified.")
