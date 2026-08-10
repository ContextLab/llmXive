"""
Pytest configuration and fixtures for the Molecular Toxicity Prediction project.
Provides shared fixtures for project paths and test data directories.
"""
import os
import sys
import pytest
from pathlib import Path

# Determine the project root based on the standard layout:
# projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/conftest.py
# Project root is the parent of 'code'
_current_file = Path(__file__).resolve()
_code_dir = _current_file.parent
_project_root = _code_dir.parent

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root directory of the project."""
    return _project_root

@pytest.fixture(scope="session")
def code_dir() -> Path:
    """Return the 'code' directory."""
    return _code_dir

@pytest.fixture(scope="session")
def src_dir() -> Path:
    """Return the 'src' directory inside 'code'."""
    return _code_dir / "src"

@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the 'data' directory inside 'code' for test resources."""
    data_dir = _code_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

@pytest.fixture(scope="function")
def add_code_to_path(code_dir: Path):
    """Add the code directory to sys.path temporarily for imports."""
    original_path = sys.path[:]
    sys.path.insert(0, str(code_dir))
    yield
    sys.path[:] = original_path
