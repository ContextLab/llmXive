"""
Basic sanity tests for the core utilities created in T001.

They verify that:
* The memory‑monitor raises an error when a dummy allocation exceeds the
  hard 7 GB limit.
* The deterministic seed helper produces reproducible NumPy random numbers.
"""

import pytest
from code.utils.memory_monitor import run_with_limit, MemoryLimitExceededError
from code.utils.seed import set_seed
import numpy as np

def test_memory_limit_exceeded():
    # The default limit is 7 GB; requesting 8 GB should raise.
    with pytest.raises(MemoryLimitExceededError):
        run_with_limit(limit_gb=8)

def test_seed_reproducibility():
    set_seed(12345)
    a = np.random.rand()
    set_seed(12345)
    b = np.random.rand()
    assert a == b, "NumPy random numbers should be identical after resetting the seed"
