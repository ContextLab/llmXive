"""
Tests for deterministic seed handling (code/utils/seed.py).
"""

import random
import numpy as np
import torch

from utils.seed import set_seed, get_seed_value, DEFAULT_SEED


def _sample_values():
    """Return a tuple of random values from the three libraries."""
    return (
        random.random(),
        np.random.rand(),
        torch.rand(1).item(),
    )


def test_set_seed_reproducibility():
    """
    Setting the same seed twice must produce identical sequences
    across random, numpy, and torch.
    """
    seed = 12345
    set_seed(seed)
    vals1 = _sample_values()

    # Reset the seed to the same value and sample again
    set_seed(seed)
    vals2 = _sample_values()

    assert vals1 == vals2, "Values differ despite identical seeds"


def test_default_seed():
    """
    When no seed is provided, the default seed constant should be used.
    """
    # Ensure environment variable does not interfere
    import os
    os.environ.pop('SEED', None)

    set_seed()
    assert get_seed_value() == DEFAULT_SEED
