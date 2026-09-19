"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Ensure the project root is in the path for imports
@pytest.fixture(scope="session", autouse=True)
def setup_project_paths():
    """Add project root to sys.path if not already present."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)

@pytest.fixture
def sample_dataset_dir(temp_dir):
    """Create a mock dataset directory structure."""
    data_dir = Path(temp_dir) / "datasets"
    data_dir.mkdir()
    # Create a dummy CSV file
    dummy_file = data_dir / "dummy.csv"
    dummy_file.write_text("id,value\n1,10\n2,20\n3,30\n")
    return data_dir
