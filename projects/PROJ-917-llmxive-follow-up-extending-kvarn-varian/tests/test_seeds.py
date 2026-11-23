"""
Tests for the global random seed management utilities.
"""

import random
import numpy as np

from utils.seeds import set_global_seed, reset_seed, get_seed, ensure_seed_set

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def test_global_seed_reproducibility():
    """
    Verify that setting the global seed produces deterministic outputs
    across numpy, random, and torch (if available).
    """
    seed = 123456

    # First run
    set_global_seed(seed)
    np_vals_1 = np.random.rand(5)
    rand_val_1 = random.random()
    if TORCH_AVAILABLE:
        torch_vals_1 = torch.randn(3).numpy()

    # Reset and set again to the same seed
    reset_seed()
    set_global_seed(seed)
    np_vals_2 = np.random.rand(5)
    rand_val_2 = random.random()
    if TORCH_AVAILABLE:
        torch_vals_2 = torch.randn(3).numpy()

    # Assertions
    assert np.allclose(np_vals_1, np_vals_2), "NumPy sequences differ after reseeding"
    assert rand_val_1 == rand_val_2, "random.random() values differ after reseeding"
    if TORCH_AVAILABLE:
        assert np.allclose(torch_vals_1, torch_vals_2), "Torch tensors differ after reseeding"

    # Ensure get_seed returns the correct value
    assert get_seed() == seed, "get_seed() did not return the expected seed"

    # Ensure ensure_seed_set returns the existing seed without changing it
    ensure_seed_set()
    assert get_seed() == seed, "ensure_seed_set() altered the seed unexpectedly"