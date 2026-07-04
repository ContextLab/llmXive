"""
Pytest configuration and shared fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
# Assumes this file is at: projects/PROJ-713-.../tests/conftest.py
# and we need to add: projects/PROJ-713-.../code to sys.path
@pytest.fixture(scope="session", autouse=True)
def add_project_root_to_path():
    """Add the project root to sys.path to allow imports from code/."""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    code_path = project_root / "code"
    
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    
    yield

# Example fixture for a temporary data directory
@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary directory for data processing tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir