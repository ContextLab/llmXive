import os
import pytest
from pathlib import Path
import shutil

from code.setup_directories import main

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to act as the project root for testing."""
    return tmp_path

def test_directories_created(temp_project_root):
    """Test that the required directories are created by the main function."""
    # Change to the temp directory to simulate running from project root
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)

    try:
        # Run the setup function
        main()

        # Verify directories exist
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests"
        ]

        for dir_name in required_dirs:
            dir_path = temp_project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_idempotent_creation(temp_project_root):
    """Test that running the script twice does not raise errors."""
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)

    try:
        # Run twice
        main()
        main() # Should not raise

        # Verify existence
        assert (temp_project_root / "code").exists()
        assert (temp_project_root / "data/raw").exists()
    finally:
        os.chdir(original_cwd)
