"""
Unit tests for ``src.utils.random_seed``.
"""

import random
import numpy as np
import torch

from src.utils.random_seed import set_random_seed


def _sample_values() -> tuple[float, float, float]:
    """
    Generate a single random value from each library after the seed has been set.

    Returns
    -------
    tuple[float, float, float]
        (random.random(), np.random.rand(), torch.rand(1).item())
    """
    r = random.random()
    n = np.random.rand()
    t = torch.rand(1).item()
    return r, n, t


def test_set_random_seed_is_deterministic() -> None:
    """
    Verify that calling ``set_random_seed`` with the same seed
    produces identical sequences across ``random``, ``numpy`` and ``torch``.
    """
    seed = 123456

    # First run
    set_random_seed(seed)
    first = _sample_values()

    # Reset the seed and sample again
    set_random_seed(seed)
    second = _sample_values()

    assert first == second, "Sequences differ despite identical seeds"