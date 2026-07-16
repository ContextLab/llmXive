"""
Unit tests for configuration and seed pinning.
"""
import random
import numpy as np
from code.config import set_seed, load_config

def test_set_seed_determinism():
    """Verify that setting the seed produces deterministic results."""
    # Set seed
    set_seed(42)
    val1 = random.random()
    arr1 = np.random.rand(5)

    # Reset seed
    set_seed(42)
    val2 = random.random()
    arr2 = np.random.rand(5)

    assert val1 == val2, "Random seed not deterministic for random module"
    assert np.array_equal(arr1, arr2), "Random seed not deterministic for numpy"

def test_load_config():
    """Verify config loading works."""
    config = load_config()
    assert "random_seed" in config
    assert "fdr_threshold" in config
