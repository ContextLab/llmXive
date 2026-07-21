"""
Pytest configuration and global fixtures.
Sets the random seed to 42 for all tests to ensure reproducibility.
"""
import os
import random
import sys
from pathlib import Path

import numpy as np
import pytest

# Project root directory
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
CODE_DIR = ROOT_DIR / "code"

# Add project root to path if not already present
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

@pytest.fixture(scope="session", autouse=True)
def set_random_seed():
    """
    Autouse fixture to set the random seed for the entire test session.
    This ensures that all random operations are deterministic.
    """
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: For torch/tensorflow, specific seed setting logic would be added here
    # if those dependencies were active in the test suite.
    return seed

@pytest.fixture
def data_dir():
    """Fixture to provide the path to the data directory."""
    return DATA_DIR

@pytest.fixture
def code_dir():
    """Fixture to provide the path to the code directory."""
    return CODE_DIR

@pytest.fixture
def temp_output_dir(tmp_path):
    """Fixture to provide a temporary directory for output files during tests."""
    return tmp_path
