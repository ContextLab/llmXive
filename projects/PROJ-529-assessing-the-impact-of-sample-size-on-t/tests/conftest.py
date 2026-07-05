"""
Pytest configuration and fixtures for the project.

This file provides shared fixtures and configuration for both
unit and integration tests.
"""
import pytest
import os
import sys
from pathlib import Path

# Add the code directory to the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add code directory to sys.path for imports."""
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "output").mkdir()
    return data_dir

@pytest.fixture
def temp_code_dir(tmp_path):
    """Create a temporary code directory for testing."""
    code_dir = tmp_path / "code"
    code_dir.mkdir()
    (code_dir / "utils").mkdir()
    (code_dir / "models").mkdir()
    (code_dir / "tests").mkdir()
    return code_dir
