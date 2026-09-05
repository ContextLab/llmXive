"""
Pytest configuration and shared fixtures for the llmXive test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the src directory is on the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add the code/src directory to sys.path for tests."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    # Optional: cleanup if needed, though usually not required for path insertion

@pytest.fixture
def test_data_dir():
    """Provide the path to the test data directory."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    return data_dir
