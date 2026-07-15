"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Add the project root to sys.path for imports."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup if necessary
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def data_dir():
    """Provide path to the data directory."""
    return Path(__file__).parent.parent / "data"

@pytest.fixture
def code_dir():
    """Provide path to the code directory."""
    return Path(__file__).parent.parent / "code"
