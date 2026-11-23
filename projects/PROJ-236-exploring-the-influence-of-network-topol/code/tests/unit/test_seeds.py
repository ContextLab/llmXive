import numpy as np
import pytest

from utils.seeds import set_global_seed, get_global_seed


def test_seed_reproducibility():
    """Verify that resetting the same seed yields identical random numbers."""
    seed = 42
    set_global_seed(seed)
    first = np.random.rand(10)

    # Reset the seed to the same value and generate again
    set_global_seed(seed)
    second = np.random.rand(10)

    np.testing.assert_allclose(first, second)


def test_get_global_seed():
    """Check that the helper reports the current seed correctly."""
    seed = 7
    set_global_seed(seed)
    assert get_global_seed() == seed