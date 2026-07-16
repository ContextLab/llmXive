"""
Tests to verify the project directory structure created by T001.

These tests ensure that the required folders exist after the setup script runs.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root(tmp_path):
    """
    Create a temporary directory to simulate the project root for testing.
    We change the current working directory to this temp path for the test duration.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_setup_script_creates_directories(project_root):
    """Test that the setup script creates the required directory structure."""
    # Import the function to test (simulating the script execution)
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
    
    # We can't easily import the function if it's in a script, so we run the logic directly
    # or we assume the script has been run. Since we are testing the *result* of T001,
    # we verify the existence of the directories that T001 should have created.
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_nested_directories_exist(project_root):
    """Test that nested directories (e.g., data/raw) are created correctly."""
    # This is implicitly covered by test_setup_script_creates_directories,
    # but we can be explicit about the nested structure.
    assert (project_root / "data" / "raw").exists()
    assert (project_root / "data" / "processed").exists()
    assert (project_root / "data" / "reports").exists()