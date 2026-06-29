"""
Tests for the seed management module.
"""

import random
import numpy as np

import sys
sys.path.insert(0, 'code')

from seeds import set_seed, get_seed_value, SEED_VALUE


def test_seed_value_constant():
    """Test that the documented seed value is 42."""
    assert SEED_VALUE == 42, f"Expected SEED_VALUE to be 42, got {SEED_VALUE}"
    assert get_seed_value() == 42, "get_seed_value() should return 42"


def test_set_seed_default():
    """Test that set_seed() uses the default seed value of 42."""
    set_seed()
    # Generate a random number and check it's deterministic
    val1 = random.random()
    val2 = np.random.rand()

    # Reset and verify same values
    set_seed()
    assert random.random() == val1, "Random seed not set correctly"
    assert np.random.rand() == val2, "Numpy seed not set correctly"


def test_set_seed_custom():
    """Test that set_seed() accepts custom seed values."""
    custom_seed = 12345
    set_seed(custom_seed)
    val1 = random.random()
    val2 = np.random.rand()

    # Reset with same custom seed
    set_seed(custom_seed)
    assert random.random() == val1, "Custom random seed not working"
    assert np.random.rand() == val2, "Custom numpy seed not working"