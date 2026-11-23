"""
Pytest configuration and fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add src to path for tests."""
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield

@pytest.fixture
def test_data_dir(tmp_path):
    """Provide a temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
