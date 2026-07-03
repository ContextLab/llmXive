"""
Tests for the directory setup script.
"""
import os
import shutil
import tempfile
import pytest
import sys

# Add the parent directory to the path to import the script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.setup_directories import create_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that create_directories creates all expected folders."""
    # Expected directories relative to temp_project_root
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "results/figures",
        "results/reports",
        "tests",
        "state",
        "logs"
    ]

    # Verify none exist initially (except maybe if they were created by other tests,
    # but in a fresh temp dir they shouldn't)
    for d in expected_dirs:
        assert not os.path.exists(d), f"Directory {d} should not exist before test."

    # Run the function
    created_count = create_directories()

    # Verify all exist now
    for d in expected_dirs:
        assert os.path.exists(d), f"Directory {d} was not created."
        assert os.path.isdir(d), f"Path {d} is not a directory."

    # Check count (should be equal to number of expected dirs)
    assert created_count == len(expected_dirs)

def test_create_directories_idempotent(temp_project_root):
    """Test that running create_directories twice doesn't fail."""
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "results/figures",
        "results/reports",
        "tests",
        "state",
        "logs"
    ]

    # Run once
    create_directories()

    # Verify they exist
    for d in expected_dirs:
        assert os.path.exists(d)

    # Run again - should not raise an error
    count_second_run = create_directories()

    # Second run should create 0 new directories
    assert count_second_run == 0
