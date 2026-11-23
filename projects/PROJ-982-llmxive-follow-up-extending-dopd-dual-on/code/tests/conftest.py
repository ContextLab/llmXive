"""
Pytest configuration and fixtures for llmXive DOPD project.
Provides strict seed pinning to ensure deterministic reproducibility across runs.
"""
import os
import random
import hashlib
from typing import Optional

import numpy as np
import pytest


def _set_seed(seed: int) -> None:
    """
    Globally set random seeds for Python's random, numpy, and environment variables.
    This ensures deterministic behavior for all stochastic operations.
    """
    # Python random module
    random.seed(seed)
    
    # NumPy random state
    np.random.seed(seed)
    
    # Set environment variable for reproducibility (used by some libraries)
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # If torch is available (optional dependency), set its seeds too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        # PyTorch not installed, skip
        pass


@pytest.fixture(scope="function", autouse=True)
def seed_everything(request) -> None:
    """
    Automatically seed the environment before each test function.
    
    The seed is determined by:
    1. An explicit `@pytest.mark.seed(N)` marker on the test function (if present).
    2. The `SEED` environment variable (if set).
    3. A default fixed seed of 42.
    
    This ensures that every test run is deterministic and reproducible.
    """
    # Check for explicit marker
    marker = request.node.get_closest_marker("seed")
    if marker and marker.args:
        seed = marker.args[0]
    # Check environment variable
    elif "SEED" in os.environ:
        seed = int(os.environ["SEED"])
    # Default seed
    else:
        seed = 42
    
    _set_seed(seed)


@pytest.fixture
def deterministic_seed() -> int:
    """
    Returns the fixed seed value used for this test run.
    Useful for tests that need to verify the seed was applied correctly.
    """
    marker = pytest.mark.seed(42)  # Default fallback for fixture logic
    if hasattr(pytest, "config"):
        # Pytest < 3.0 compatibility (rare)
        pass
    
    if "SEED" in os.environ:
        return int(os.environ["SEED"])
    return 42


@pytest.fixture
def fixed_seed_42() -> int:
    """
    Explicitly returns the canonical seed 42 for tests requiring a specific known state.
    """
    return 42


@pytest.fixture
def rng_generator(fixed_seed_42):
    """
    Returns a deterministic numpy RandomState generator initialized with the fixed seed.
    Useful for tests that need to pass a specific RNG instance to functions.
    """
    return np.random.RandomState(fixed_seed_42)


@pytest.fixture
def python_rng(fixed_seed_42):
    """
    Returns a deterministic Python random.Random instance initialized with the fixed seed.
    """
    return random.Random(fixed_seed_42)


# Helper function to derive a seed from a string (e.g., for scenario-based seeding)
def derive_seed_from_string(label: str, base_seed: int = 42) -> int:
    """
    Derives a deterministic integer seed from a string label.
    Useful for creating reproducible seeds for specific scenarios or configurations.
    """
    hash_obj = hashlib.sha256(f"{base_seed}:{label}".encode())
    return int(hash_obj.hexdigest(), 16) % (2**32)


@pytest.fixture
def scenario_seed():
    """
    Factory fixture to derive seeds from scenario names.
    Usage: 
      def test_my_scenario(scenario_seed):
          seed = scenario_seed("my_scenario_name")
          ...
    """
    def _derive(label: str, base: int = 42) -> int:
        return derive_seed_from_string(label, base)
    return _derive