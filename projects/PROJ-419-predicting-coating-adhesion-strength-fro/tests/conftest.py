"""
Pytest configuration and fixtures for the llmXive project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root directory path."""
    return project_root

@pytest.fixture(scope="session")
def data_dir(project_root_path):
    """Return the data directory path."""
    return project_root_path / "data"

@pytest.fixture(scope="session")
def code_dir(project_root_path):
    """Return the code directory path."""
    return project_root_path / "code"

@pytest.fixture(scope="session")
def state_dir(project_root_path):
    """Return the state directory path."""
    return project_root_path / "state"
