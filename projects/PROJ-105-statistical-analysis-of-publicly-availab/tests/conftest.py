"""
Pytest configuration and base fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure project root is in path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    yield
    sys.path.remove(str(project_root))

@pytest.fixture
def data_dir():
    """Path to the data directory."""
    return Path("data")

@pytest.fixture
def processed_data_dir():
    """Path to the processed data directory."""
    return Path("data/processed")

@pytest.fixture
def results_dir():
    """Path to the results directory."""
    return Path("data/results")

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def sample_delay_data():
    """
    Generate a small sample of delay data for testing.
    This is for unit testing logic, NOT for production analysis.
    """
    return [10, 15, 20, 30, 45, 60, 120, 300, 600]