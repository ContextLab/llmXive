"""
Unit tests for the deterministic seed utilities (code/utils/seed.py).
"""

import random
import numpy as np
import torch

from utils.seed import set_seed, get_seed_value, DEFAULT_SEED

def test_set_seed_reproducibility():
    """After setting a seed, successive calls to RNGs must be deterministic."""
    seed = 42
    set_seed(seed)

    # Record first draws
    py_rand_1 = random.random()
    np_rand_1 = np.random.rand()
    torch_rand_1 = torch.rand(1).item()

    # Reset seed and draw again – should match first draws
    set_seed(seed)
    py_rand_2 = random.random()
    np_rand_2 = np.random.rand()
    torch_rand_2 = torch.rand(1).item()

    assert py_rand_1 == py_rand_2, "Python random not reproducible"
    assert np_rand_1 == np_rand_2, "NumPy random not reproducible"
    assert torch_rand_1 == torch_rand_2, "PyTorch random not reproducible"

def test_get_seed_value_defaults():
    """When no SEED env var is set, get_seed_value should return DEFAULT_SEED."""
    # Ensure environment variable is unset for the test
    import os
    os.environ.pop("SEED", None)

    assert get_seed_value() == DEFAULT_SEED
