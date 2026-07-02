"""
Tests for the directory setup script.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.setup_dirs import create_directory_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_creates_required_directories(temp_project_root):
    """Test that all required directories are created."""
    create_directory_structure()

    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "output",
        "output/plots",
        "tests",
    ]

    for dir_name in required_dirs:
        full_path = os.path.join(temp_project_root, dir_name)
        assert os.path.isdir(full_path), f"Directory {dir_name} was not created"

def test_handles_existing_directories(temp_project_root):
    """Test that the script handles existing directories gracefully."""
    # Create some directories manually first
    os.makedirs("code")
    os.makedirs("data/raw")

    # Run setup again
    create_directory_structure()

    # Verify they still exist
    assert os.path.isdir("code")
    assert os.path.isdir("data/raw")
    assert os.path.isdir("data/processed")