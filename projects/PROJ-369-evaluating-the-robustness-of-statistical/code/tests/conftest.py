"""
Pytest configuration and shared fixtures.
"""
import pytest
import os
import sys
from pathlib import Path

# Add the src directory to the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add the src directory to sys.path for all tests."""
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    # Cleanup not strictly necessary as sys.path is process-local, 
    # but good practice in some scenarios.
    if str(src_path) in sys.path:
        sys.path.remove(str(src_path))

@pytest.fixture
def test_data_dir():
    """Provide a path to the test data directory."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "test_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def output_dir():
    """Provide a temporary output directory for test artifacts."""
    import tempfile
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup could be added here if needed, but often left to OS or explicit test logic