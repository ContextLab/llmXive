"""
Pytest configuration file.
Contains fixtures and setup for the test suite.
"""
import pytest
import sys
from pathlib import Path

# Ensure the src directory is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    root = Path(__file__).parent.parent
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    if str(src_path) in sys.path:
        sys.path.remove(str(src_path))

@pytest.fixture
def sample_data_path(tmp_path):
    """Create a temporary directory with sample data files if needed."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
