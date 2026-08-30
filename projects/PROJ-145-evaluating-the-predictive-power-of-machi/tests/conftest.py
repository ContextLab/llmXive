"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
import sys
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield

@pytest.fixture
def project_root():
    """Return the project root directory path."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"

@pytest.fixture
def code_dir(project_root):
    """Return the code directory path."""
    return project_root / "code"
