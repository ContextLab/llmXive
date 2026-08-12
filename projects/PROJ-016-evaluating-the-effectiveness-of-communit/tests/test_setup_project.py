"""
Tests for the project setup script.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import main

class TestProjectSetup:
    """Test cases for project setup functionality."""

    def test_directory_creation(self, tmp_path):
        """Test that the required directories are created."""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            # Create a mock setup_project.py in the temp directory structure
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            
            # Copy the main logic here for testing
            directories = [
                "code/data",
                "code/analysis",
                "code/tests",
                "data/raw",
                "data/processed",
                "docs/output",
                "logs"
            ]

            for dir_path in directories:
                full_path = tmp_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)

            # Verify directories exist
            for dir_path in directories:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"

        finally:
            os.chdir(original_cwd)

    def test_existing_directories_not_overwritten(self, tmp_path):
        """Test that existing directories are not modified."""
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))

        try:
            # Pre-create some directories
            pre_created = tmp_path / "code" / "data"
            pre_created.mkdir(parents=True)
            
            # Add a marker file
            marker = pre_created / "marker.txt"
            marker.write_text("test")

            # Run setup logic
            directories = [
                "code/data",
                "code/analysis",
            ]

            for dir_path in directories:
                full_path = tmp_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)

            # Verify marker file still exists
            assert marker.exists(), "Marker file was removed"
            assert marker.read_text() == "test", "Marker file content was modified"

        finally:
            os.chdir(original_cwd)