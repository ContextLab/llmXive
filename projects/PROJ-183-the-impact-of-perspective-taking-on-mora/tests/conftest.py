"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_project_root():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
    if str(root) in sys.path:
        sys.path.remove(str(root))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data layout."""
    raw = tmp_path / "data" / "raw"
    processed = tmp_path / "data" / "processed"
    human = tmp_path / "data" / "human"
    raw.mkdir(parents=True)
    processed.mkdir(parents=True)
    human.mkdir(parents=True)
    return tmp_path / "data"
