"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Add the project root to sys.path to allow imports from code/."""
    root_dir = Path(__file__).parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    
    yield
    
    if str(root_dir) in sys.path:
        sys.path.remove(str(root_dir))

@pytest.fixture(scope="session")
def project_root():
    """Return the path to the project root."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture(scope="session")
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    return data_dir / "raw"

@pytest.fixture(scope="session")
def code_dir(project_root):
    """Return the path to the code directory."""
    return project_root / "code"