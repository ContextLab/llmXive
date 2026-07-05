"""
Pytest configuration and fixtures.
"""
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

@pytest.fixture
def project_root_path():
    """Return the project root directory."""
    return project_root

@pytest.fixture
def data_dir(project_root_path):
    """Return the data directory."""
    return project_root_path / "data"

@pytest.fixture
def results_dir(project_root_path):
    """Return the results directory."""
    return project_root_path / "results"

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def sample_json_data():
    """Provide sample JSON data for testing."""
    return {
        "key": "value",
        "number": 42,
        "list": [1, 2, 3]
    }
