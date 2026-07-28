"""
Pytest configuration and fixtures for the llmXive research pipeline.

This module ensures reproducible experiments by pinning random seeds
at the start of every test session.
"""
import os
import random
import sys
from pathlib import Path

import numpy as np
import pytest

# Define the project root to ensure relative imports work correctly
# when tests are run from the 'tests' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Fixed seed for reproducibility across all random number generators
# This ensures that any stochastic process in the pipeline (sampling,
# shuffling, initialization) yields identical results across runs.
SEED = 42


@pytest.fixture(scope="session", autouse=True)
def set_random_seed():
    """
    Autouse fixture to set global random seeds for reproducibility.
    
    This runs automatically at the start of the test session.
    It seeds:
    - Python's built-in random module
    - NumPy's random number generator
    - Environment variable for other libraries (e.g., PyTorch, TensorFlow)
    
    Note: This does not seed libraries that require specific initialization
    calls (like torch.manual_seed) inside their own setup, but it covers
    the standard data processing stack.
    """
    random.seed(SEED)
    np.random.seed(SEED)
    os.environ["PYTHONHASHSEED"] = str(SEED)
    
    # Yield control to the test runner
    yield
    
    # Optional: Reset seeds after tests if needed for isolation
    # (usually not required for session scope)

@pytest.fixture(scope="session")
def seed_value():
    """
    Provides the fixed seed value used in the session.
    
    Useful for tests that need to explicitly verify they are using
    the correct seed or for generating expected values in unit tests.
    """
    return SEED
