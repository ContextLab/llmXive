"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path so imports work during tests
# Assumes tests are run from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def project_root():
    """Return the path to the project root directory."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    return data_dir / "raw"

@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture(scope="session")
def code_dir(project_root):
    """Return the path to the code directory."""
    return project_root / "code"