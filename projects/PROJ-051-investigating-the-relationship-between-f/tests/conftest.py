"""
Pytest configuration and fixtures for PROJ-051.
"""
import pytest
import numpy as np
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import PROJECT_ROOT, DATA_DIR

@pytest.fixture
def sample_velocity_field():
    """Generate a sample velocity field for testing."""
    np.random.seed(42)
    shape = (64, 64, 64, 3)  # Small grid for testing
    return np.random.randn(*shape)

@pytest.fixture
def sample_vorticity_field():
    """Generate a sample vorticity field for testing."""
    np.random.seed(42)
    shape = (64, 64, 64)
    return np.random.randn(*shape)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture(autouse=True)
def setup_environment():
    """Setup test environment."""
    # Ensure required directories exist
    Path(PROJECT_ROOT).mkdir(parents=True, exist_ok=True)
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup after test (optional)
