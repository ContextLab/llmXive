"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project code directory to the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Ensure project code is importable."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if necessary
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def project_root():
    """Return the root path of the project."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture
def results_dir(project_root):
    """Return the path to the results directory."""
    return project_root / "results"
