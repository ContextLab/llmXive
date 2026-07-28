"""
Pytest configuration and shared fixtures for the Bounded Confidence project.
"""
import os
import sys
import random
from pathlib import Path

import numpy as np
import pytest

# Add project root to path to ensure imports work from tests/
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Global random seed for reproducibility (FR-001)
# This seed is used by the main simulation scripts and can be overridden
# via environment variable for testing purposes.
BASE_SEED = int(os.getenv("PROJECT_BASE_SEED", "42"))


@pytest.fixture(scope="session", autouse=True)
def set_global_seeds():
    """
    Fixture to set global random seeds at the start of the test session.
    Ensures reproducibility across the entire test run.
    """
    random.seed(BASE_SEED)
    np.random.seed(BASE_SEED)
    # Note: If using other libraries like torch, set their seeds here too.


@pytest.fixture
def project_root_path():
    """Returns the Path to the project root directory."""
    return project_root


@pytest.fixture
def data_dir(project_root_path):
    """Returns the Path to the data directory."""
    return project_root_path / "data"


@pytest.fixture
def contracts_dir(project_root_path):
    """Returns the Path to the contracts directory."""
    return project_root_path / "code" / "contracts"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Creates a temporary directory for test outputs."""
    return tmp_path
