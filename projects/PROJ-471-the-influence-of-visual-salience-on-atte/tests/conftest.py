"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    root = Path(__file__).parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

# Setup temporary directories for test runs if needed
@pytest.fixture
def test_data_dir(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
