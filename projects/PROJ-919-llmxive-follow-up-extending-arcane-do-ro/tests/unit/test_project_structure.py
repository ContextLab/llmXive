"""
Unit tests for project structure setup.
Verifies that the required directories and placeholder files exist.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys
import shutil

# Add the project root to the path to import setup_project_structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from setup_project_structure import setup_directories

class TestProjectStructure:
    """Tests for the project structure creation logic."""

    def test_setup_directories_creates_required_folders(self, tmp_path):
        """Verify that all required directories are created."""
        # Change to tmp_path for the test
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Run the setup
            setup_directories()

            # Verify core directories exist
            required_dirs = [
                "src", "tests", "data", 
                "specs/001-gene-regulation", 
                "data/raw", "data/derived", "data/gold_standard",
                "artifacts", "figures"
            ]

            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

        finally:
            os.chdir(original_cwd)

    def test_setup_directories_creates_placeholder_files(self, tmp_path):
        """Verify that placeholder files are created to ensure git tracking."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            setup_directories()

            required_files = [
                "src/__init__.py",
                "tests/__init__.py",
                "data/raw/.gitkeep",
                "specs/001-gene-regulation/README.md"
            ]

            for file_name in required_files:
                file_path = tmp_path / file_name
                assert file_path.exists(), f"Placeholder file {file_name} was not created"

        finally:
            os.chdir(original_cwd)

    def test_nested_directories_exist(self, tmp_path):
        """Verify that nested directories like src/services and tests/unit exist."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            setup_directories()

            nested_dirs = [
                "src/lib", "src/services", "src/analysis", "src/cli",
                "tests/unit", "tests/integration",
                "specs/001-gene-regulation/contracts"
            ]

            for dir_name in nested_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Nested directory {dir_name} was not created"

        finally:
            os.chdir(original_cwd)