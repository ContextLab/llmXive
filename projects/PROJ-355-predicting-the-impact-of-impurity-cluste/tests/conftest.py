"""
Pytest configuration and fixtures for the project.

Provides shared fixtures for testing across unit and integration tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path so we can import code modules
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Automatically add the project root to sys.path for imports."""
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    yield tmp_path
