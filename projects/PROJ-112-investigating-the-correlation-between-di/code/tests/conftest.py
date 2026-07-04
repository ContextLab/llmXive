"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def setup_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"

@pytest.fixture
def processed_dir(data_dir):
    """Return the processed data directory path."""
    return data_dir / "processed"

@pytest.fixture
def results_dir(processed_dir):
    """Return the results directory path."""
    return processed_dir / "results"
