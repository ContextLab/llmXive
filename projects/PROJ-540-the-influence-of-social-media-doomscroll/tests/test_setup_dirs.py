"""
T001a: Tests for directory structure creation.
"""
import os
import pytest
import shutil
import tempfile
import sys

# Add parent directory to path to import setup_dirs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from code.setup_dirs import create_directories

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to simulate project root."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_directories_created(temp_project_root):
    """Verify that all required directories are created."""
    # Remove existing directories if any (simulating fresh start)
    dirs_to_check = ["data/raw", "data/processed", "code", "outputs", "tests"]
    for d in dirs_to_check:
        if os.path.exists(d):
            shutil.rmtree(d)

    # Run the creation function
    create_directories()

    # Verify each directory exists
    for d in dirs_to_check:
        assert os.path.isdir(d), f"Directory {d} was not created"

def test_directories_idempotent(temp_project_root):
    """Verify that running the script again doesn't fail if dirs exist."""
    # First run
    create_directories()
    # Second run should not raise errors
    create_directories()