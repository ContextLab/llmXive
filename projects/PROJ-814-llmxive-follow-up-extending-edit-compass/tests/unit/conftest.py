"""
Pytest configuration and shared fixtures for unit tests.
"""
import os
import sys
import pytest

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    yield
    if root_dir in sys.path:
        sys.path.remove(root_dir)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory structure for testing."""
    raw_dir = tmp_path / "data" / "raw"
    filtered_dir = tmp_path / "data" / "filtered"
    scores_dir = tmp_path / "data" / "scores"
    
    raw_dir.mkdir(parents=True)
    filtered_dir.mkdir(parents=True)
    scores_dir.mkdir(parents=True)
    
    return {
        "raw": str(raw_dir),
        "filtered": str(filtered_dir),
        "scores": str(scores_dir),
        "root": str(tmp_path)
    }