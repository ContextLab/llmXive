"""
Pytest configuration and shared fixtures for the project.
"""
import os
import sys
import random
import numpy as np
import pytest
from pathlib import Path

# Add the project root to the path if not already present
# This ensures imports like `from utils.metrics import ...` work in tests
project_root = Path(__file__).parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

@pytest.fixture(scope="session")
def global_seed():
    """
    Fixture providing a fixed global seed for reproducible experiments.
    Used by network generation and simulation tasks.
    """
    return 42

@pytest.fixture(scope="function")
def set_seed(global_seed):
    """
    Fixture to set random seeds before each test function.
    Ensures deterministic behavior for tests involving randomness.
    """
    random.seed(global_seed)
    np.random.seed(global_seed)
    yield
    # Reset is optional as we set it again in next test, but good practice
    random.seed(global_seed)
    np.random.seed(global_seed)
