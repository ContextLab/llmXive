"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
    if str(root) in sys.path:
        sys.path.remove(str(root))

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture to provide a temporary directory for test artifacts."""
    yield tmp_path