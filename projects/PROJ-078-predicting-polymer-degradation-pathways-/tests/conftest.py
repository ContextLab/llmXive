"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_project_root():
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
    if str(root) in sys.path:
        sys.path.remove(str(root))

@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test outputs."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
