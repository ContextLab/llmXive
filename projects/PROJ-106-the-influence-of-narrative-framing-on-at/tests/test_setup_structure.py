"""
Test suite to verify that the project structure setup script works correctly.
"""
import os
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from setup_project_structure import create_directories

def test_directory_creation(tmp_path):
    """
    Test that create_directories creates the required folder structure
    when run in a temporary directory.
    """
    # Change to the temporary directory to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Run the setup function
        # We need to monkeypatch Path.cwd() or call logic directly if possible.
        # Since the function uses Path.cwd(), we rely on the os.chdir above.
        create_directories()

        # Verify expected directories exist
        expected_dirs = [
            "code",
            "data",
            "data/raw",
            "data/processed",
            "data/stimuli",
            "data/ethics",
            "tests",
            "specs",
            "docs"
        ]

        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created."
            assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory."

    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """
    Test that running the setup script twice does not raise errors
    and leaves the structure intact.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Run twice
        create_directories()
        create_directories()

        # Verify structure still exists
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data/processed").exists()

    finally:
        os.chdir(original_cwd)
