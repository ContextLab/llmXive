"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
import tempfile
import shutil

# Add project root to path for imports
@pytest.fixture(autouse=True)
def setup_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    yield
    # Cleanup if needed

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)

@pytest.fixture
def sample_data_dir(temp_dir):
    """Create a temporary data directory structure."""
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir
