"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the code directory is on the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the project code directory to sys.path for tests."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield
    
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def project_root():
    """Return the root path of the project."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture
def test_data_dir(data_dir):
    """Return the path to the test data directory."""
    return data_dir / "test"

@pytest.fixture
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    return data_dir / "raw"