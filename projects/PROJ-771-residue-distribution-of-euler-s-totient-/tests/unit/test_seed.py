"""
Unit tests for the ``code.seed`` module.

The tests verify that:
1. ``pin_seeds`` correctly seeds both ``random`` and ``numpy.random``.
2. ``get_seed`` returns the value supplied to ``pin_seeds``.
3. Attempting to retrieve the seed before it has been set raises an error.
"""

import random
from unittest import mock

import numpy as np
import pytest

# Import the module under test.
from code.seed import pin_seeds, get_seed


def test_pin_seeds_affects_random_and_numpy():
    """The RNGs should produce reproducible values after pinning."""
    test_seed = 12345
    pin_seeds(test_seed)

    # Generate a few values from both libraries.
    py_vals = [random.random() for _ in range(3)]
    np_vals = np.random.random(3).tolist()

    # Reset the seed and generate again – values must match.
    pin_seeds(test_seed)
    py_vals_repeat = [random.random() for _ in range(3)]
    np_vals_repeat = np.random.random(3).tolist()

    assert py_vals == py_vals_repeat, "Python random values differ after reseeding"
    assert np_vals == np_vals_repeat, "NumPy random values differ after reseeding"


def test_get_seed_returns_correct_value():
    """``get_seed`` should return the most recent seed."""
    for seed in (0, 42, 999):
        pin_seeds(seed)
        assert get_seed() == seed


def test_get_seed_before_pinning_raises():
    """Calling ``get_seed`` before any seed is set must raise."""
    # Reload the module to ensure a fresh state where no seed has been set.
    with mock.patch("code.seed._current_seed", None):
        with pytest.raises(RuntimeError, match="Seed has not been set"):
            get_seed()