"""
Unit tests for ``code.utils.seed``.

The tests verify that ``set_seed`` produces deterministic behaviour
across the standard random libraries (``random``, ``numpy`` and ``torch``).
"""

import random

import numpy as np
import torch

from utils.seed import set_seed, get_seed_value, DEFAULT_SEED


def _sample_random_values():
    """
    Generate a small collection of random values from the three libraries.
    """
    return {
        "python_random": random.random(),
        "numpy_random": np.random.rand(),
        "torch_random": torch.rand(1).item(),
    }


def test_set_seed_reproducibility():
    """
    After calling ``set_seed`` with a fixed integer, the sequence of
    random numbers from each library must be identical on a second call
    with the same seed.
    """
    seed = 42

    # First run
    set_seed(seed)
    values_first = _sample_random_values()

    # Reset the RNGs with the same seed
    set_seed(seed)
    values_second = _sample_random_values()

    assert values_first == values_second, "RNG sequences differ despite same seed"


def test_default_seed():
    """
    ``get_seed_value`` should return the default seed when the ``SEED``
    environment variable is unset.
    """
    # Ensure the environment variable is not set for this test
    if "SEED" in os.environ:
        del os.environ["SEED"]

    assert get_seed_value() == DEFAULT_SEED


def test_set_seed_returns_value():
    """
    ``set_seed`` must return the seed it actually set.
    """
    returned = set_seed(12345)
    assert returned == 12345
    assert get_seed_value() == 12345
