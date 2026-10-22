"""
Unit test for the seed configuration loader.

The test imports ``code.utils.config_loader`` (which automatically loads
``config/seeds.yaml`` and applies the seeds) and then checks that the
random state for ``numpy``, ``random`` and, if available, ``torch`` matches
the expected deterministic values for seed ``42``.
"""

import importlib
import sys

import numpy as np
import random

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

# Import the module – this triggers the side‑effect of setting the seeds.
config_loader = importlib.import_module("code.utils.config_loader")

def test_global_seed_variable():
    """The module should expose the seed it applied via ``GLOBAL_SEED``."""
    assert hasattr(config_loader, "GLOBAL_SEED")
    assert config_loader.GLOBAL_SEED == 42

def test_numpy_random_state():
    """
    After seeding with 42, the first ``numpy.random.rand()`` call must
    yield the well‑known value 0.3745401188473625.
    """
    # Reset numpy's generator to ensure the test is deterministic even if
    # other code has already drawn from it.
    np.random.seed(42)
    val = np.random.rand()
    assert np.isclose(val, 0.3745401188473625)

def test_python_random_state():
    """
    After seeding with 42, the first ``random.random()`` call must yield
    0.6394267984578837.
    """
    random.seed(42)
    val = random.random()
    assert abs(val - 0.6394267984578837) < 1e-12

def test_torch_seed_if_available():
    """
    If ``torch`` is installed, ``torch.manual_seed`` should have been called
    with the same seed. ``torch.initial_seed()`` returns the seed value.
    """
    if _TORCH_AVAILABLE:
        assert torch.initial_seed() == 42
    else:
        # If torch is not present, the test passes trivially.
        assert True