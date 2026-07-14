"""Basic sanity tests for the configuration utilities introduced in T008."""

import os
import sys
import time
import builtins

import pytest

# Import the module under test
from config import apply_random_seed, enforce_runtime_limit, RANDOM_SEED, MAX_RUNTIME_SECONDS


def test_random_seed_is_applied():
    # Change the seed and ensure reproducibility
    apply_random_seed(123)
    import random
    import numpy as np
    assert random.random() == random.Random(123).random()
    assert np.random.rand() == np.random.RandomState(123).rand()
    # Reset to default for other tests
    apply_random_seed()


@pytest.mark.skipif(sys.platform.startswith("win"), reason="SIGALRM not available on Windows")
def test_runtime_limit_raises_timeout():
    # Set a very short limit and ensure TimeoutError is raised
    enforce_runtime_limit(1)
    with pytest.raises(TimeoutError):
        time.sleep(2)


def test_environment_variables_set():
    # Ensure that applying the seed also sets PYTHONHASHSEED
    apply_random_seed()
    assert os.getenv("PYTHONHASHSEED") == str(RANDOM_SEED)
    # Ensure runtime limit env var is present on platforms without SIGALRM
    if not hasattr(os, "kill"):
        assert os.getenv("MAX_RUNTIME_SECONDS") == str(MAX_RUNTIME_SECONDS)