"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path if not already present
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Ensure the project root is in sys.path for imports."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory for data artifacts."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    yield data_dir

@pytest.fixture
def temp_state_dir(tmp_path):
    """Provide a temporary directory for state artifacts."""
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    yield state_dir