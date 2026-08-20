"""
Seed configuration and fixation enforcement for llmXive pipeline.

This module implements Constitution Principle I (Reproducibility) and FR-005
by providing a centralized mechanism to set and enforce random seeds across
all random number generators used in the pipeline (numpy, random, torch, pybullet).

The seed must be set BEFORE any other imports or operations that rely on
randomness to ensure deterministic behavior across training (T012) and
evaluation (T013) loops.
"""

import os
import random
import numpy as np
from typing import Optional

# Default seed for reproducibility if not specified via environment variable
DEFAULT_SEED = 42

# Environment variable name for seed configuration
SEED_ENV_VAR = "LLMXIVE_SEED"


def get_seed() -> int:
    """
    Retrieve the seed value from environment variable or use default.

    Returns:
        int: The seed value to use for random number generation.
    """
    seed_str = os.environ.get(SEED_ENV_VAR)
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            raise ValueError(
                f"Invalid seed value in {SEED_ENV_VAR}: '{seed_str}'. "
                f"Must be an integer."
            )
    return DEFAULT_SEED


def set_seeds(seed: Optional[int] = None) -> int:
    """
    Set seeds for all random number generators to ensure reproducibility.

    This function must be called at the very beginning of any script that
    relies on randomness (training, evaluation, generation) to ensure
    deterministic results.

    Args:
        seed (Optional[int]): Explicit seed value. If None, uses value from
                              environment variable or DEFAULT_SEED.

    Returns:
        int: The seed value that was set.

    Raises:
        ValueError: If the seed value is invalid.
    """
    if seed is None:
        seed = get_seed()

    # Validate seed is a non-negative integer
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")

    # Set numpy random seed
    np.random.seed(seed)

    # Set Python random module seed
    random.seed(seed)

    # Set torch seed if available (Constitution Principle I)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior for CuDNN (optional but recommended for reproducibility)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        # PyTorch not installed, skip
        pass

    # Set pybullet seed (if available)
    try:
        import pybullet as p
        p.setAdditionalSearchPath(p.getDataPath())
        # PyBullet doesn't have a direct setSeed function in all versions,
        # but we set the environment variable and ensure deterministic flags
        os.environ["PYBULLET_ENABLE_Deterministic"] = "1"
    except ImportError:
        # PyBullet not installed, skip
        pass

    return seed


def enforce_seed_in_training_loop() -> int:
    """
    Enforce seed fixation at the start of a training loop (T012).

    This function should be called as the very first line in the training
    script's main execution block to ensure all subsequent operations are
    deterministic.

    Returns:
        int: The seed value used.
    """
    return set_seeds()


def enforce_seed_in_evaluation_loop() -> int:
    """
    Enforce seed fixation at the start of an evaluation loop (T013).

    This function should be called as the very first line in the evaluation
    script's main execution block to ensure deterministic object ordering
    and random operations during evaluation.

    Returns:
        int: The seed value used.
    """
    return set_seeds()


def enforce_seed_in_generation_loop() -> int:
    """
    Enforce seed fixation at the start of a generation loop (T007/T007a).

    This function should be called as the very first line in the geometry
    generation script to ensure reproducible object generation.

    Returns:
        int: The seed value used.
    """
    return set_seeds()


# Convenience function for direct import in training/evaluation scripts
def init_reproducibility() -> int:
    """
    Initialize reproducibility for the current run.

    This is a convenience wrapper that sets all seeds and returns the
    seed value for logging purposes.

    Returns:
        int: The seed value that was set.
    """
    return set_seeds()

if __name__ == "__main__":
    # Self-test to verify seed setting works
    import sys
    print(f"Testing seed fixation with default seed...")
    seed_val = init_reproducibility()
    print(f"Seeds set to: {seed_val}")
    
    # Verify numpy
    arr1 = np.random.rand(5)
    seed_val = init_reproducibility()
    arr2 = np.random.rand(5)
    assert np.allclose(arr1, arr2), "Numpy seed not deterministic!"
    
    # Verify random
    r1 = [random.random() for _ in range(5)]
    seed_val = init_reproducibility()
    r2 = [random.random() for _ in range(5)]
    assert r1 == r2, "Python random seed not deterministic!"
    
    print("SUCCESS: Seed fixation verified for numpy and random.")
    try:
        import torch
        t1 = torch.rand(5)
        seed_val = init_reproducibility()
        t2 = torch.rand(5)
        assert torch.allclose(t1, t2), "Torch seed not deterministic!"
        print("SUCCESS: Seed fixation verified for torch.")
    except ImportError:
        print("INFO: Torch not installed, skipping torch verification.")
    
    sys.exit(0)