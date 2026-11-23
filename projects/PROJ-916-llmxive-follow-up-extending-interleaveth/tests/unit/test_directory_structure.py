"""
Unit tests to verify the project directory structure required by T001c.
"""
import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")

REQUIRED_DIRS = [
    "data/raw",
    "data/intermediate",
    "data/simulator_validation"
]

@pytest.fixture
def data_root():
    return DATA_ROOT

@pytest.mark.parametrize("relative_path", REQUIRED_DIRS)
def test_directory_exists(data_root, relative_path):
    """Verify that each required subdirectory exists."""
    full_path = os.path.join(data_root, relative_path)
    assert os.path.exists(full_path), f"Directory {full_path} does not exist."
    assert os.path.isdir(full_path), f"{full_path} exists but is not a directory."

def test_data_root_exists():
    """Verify the main data directory exists."""
    assert os.path.exists(DATA_ROOT), f"Data root {DATA_ROOT} does not exist."
    assert os.path.isdir(DATA_ROOT), f"{DATA_ROOT} exists but is not a directory."