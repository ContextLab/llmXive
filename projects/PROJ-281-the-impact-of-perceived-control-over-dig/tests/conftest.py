"""
Pytest configuration and fixtures.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path so imports work correctly
# This ensures we import from 'code' package, not local scripts
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest

@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root directory path."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def data_dir(project_root_path):
    """Return the data directory path."""
    return project_root_path / "data"

@pytest.fixture(scope="session")
def raw_data_dir(data_dir):
    """Return the raw data directory path."""
    return data_dir / "raw"

@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    """Return the processed data directory path."""
    return data_dir / "processed"

@pytest.fixture(scope="session")
def code_dir(project_root_path):
    """Return the code directory path."""
    return project_root_path / "code"
