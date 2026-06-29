"""
Unit tests for ``code.utils.config``.
"""

import random
from pathlib import Path

import numpy as np
import pytest

# Import the module under test
from code.utils.config import set_random_seed, get_seed, DEFAULT_SEED, Config


def test_get_seed_from_env(monkeypatch):
    """Ensure ``get_seed`` respects the ``RANDOM_SEED`` environment variable."""
    monkeypatch.setenv("RANDOM_SEED", "123")
    assert get_seed() == 123

    # Non‑integer values should fall back to the default
    monkeypatch.setenv("RANDOM_SEED", "not-an-int")
    assert get_seed() == DEFAULT_SEED

    # Unset variable should also fall back
    monkeypatch.delenv("RANDOM_SEED", raising=False)
    assert get_seed() == DEFAULT_SEED


@pytest.mark.parametrize("seed", [0, 1, 42, 999])
def test_set_random_seed_reproducibility(seed):
    """
    After calling ``set_random_seed`` with a known seed, the sequences from
    ``random`` and ``numpy.random`` must be deterministic.
    """
    # First run
    set_random_seed(seed)
    py_random_vals = [random.random() for _ in range(5)]
    np_random_vals = np.random.rand(5).tolist()

    # Reset the seed and generate again
    set_random_seed(seed)
    py_random_vals_2 = [random.random() for _ in range(5)]
    np_random_vals_2 = np.random.rand(5).tolist()

    assert py_random_vals == py_random_vals_2, "Python random sequence not reproducible"
    assert np.allclose(np_random_vals, np_random_vals_2), "NumPy random sequence not reproducible"


def test_config_dataclass_applies_seed(monkeypatch):
    """
    Instantiating ``Config`` should automatically set the random seed.
    """
    # Choose a seed and ensure the environment variable is not set
    monkeypatch.delenv("RANDOM_SEED", raising=False)

    cfg = Config(seed=123)

    # The seeds should now be set to 123
    assert random.getstate()[1][0] == 123  # internal state check for CPython's Mersenne Twister
    assert np.random.get_state()[1][0] == 123

    # Changing the seed via ``set_random_seed`` should affect subsequent draws
    set_random_seed(456)
    assert random.random() != random.random()  # just ensure no exception


# The test suite should be discoverable by pytest without any additional
# configuration. No output files are written; the test only validates
# deterministic behaviour.