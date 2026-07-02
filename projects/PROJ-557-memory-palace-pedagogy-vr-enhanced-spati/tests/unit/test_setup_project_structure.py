"""
Unit tests for the project setup script.

These tests verify that the directory structure is created correctly
and that all required directories exist.
"""

import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add the parent directory to the path to allow importing from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_directory_structure, create_gitkeep_files


class TestCreateDirectoryStructure:
    """Tests for the create_directory_structure function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        expected_dirs = [
            "data/raw",
            "data/derived",
            "code",
            "tests/unit",
            "tests/integration",
            "results",
            "data/metadata",
            "figures",
            "specs",
            "docs",
            "code/utils",
            "code/report_assets",
        ]
        
        create_directory_structure(tmp_path)
        
        for dir_name in expected_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_handles_existing_directories(self, tmp_path):
        """Verify that existing directories are not recreated."""
        # Pre-create some directories
        existing_dirs = ["data/raw", "code"]
        for dir_name in existing_dirs:
            (tmp_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        # Run the function
        create_directory_structure(tmp_path)
        
        # Verify all directories still exist
        for dir_name in existing_dirs:
            assert (tmp_path / dir_name).exists()

    def test_creates_nested_directories(self, tmp_path):
        """Verify that nested directories are created with parents."""
        nested_dir = "tests/unit"
        create_directory_structure(tmp_path)
        
        full_path = tmp_path / nested_dir
        assert full_path.exists()
        assert (tmp_path / "tests").exists()
        assert full_path.is_dir()


class TestCreateGitkeepFiles:
    """Tests for the create_gitkeep_files function."""

    def test_creates_gitkeep_in_all_directories(self, tmp_path):
        """Verify that .gitkeep files are created in all directories."""
        expected_dirs = [
            "data/raw",
            "data/derived",
            "code",
            "tests/unit",
            "tests/integration",
            "results",
            "data/metadata",
            "figures",
            "specs",
            "docs",
            "code/utils",
            "code/report_assets",
        ]
        
        # First create the directories
        create_directory_structure(tmp_path)
        
        # Then create .gitkeep files
        create_gitkeep_files(tmp_path)
        
        for dir_name in expected_dirs:
            gitkeep_path = tmp_path / dir_name / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep not found in {dir_name}"
            assert gitkeep_path.is_file(), f"{dir_name}/.gitkeep exists but is not a file"

    def test_does_not_overwrite_existing_gitkeep(self, tmp_path):
        """Verify that existing .gitkeep files are not overwritten."""
        dir_name = "data/raw"
        (tmp_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        # Create a .gitkeep with some content
        gitkeep_path = tmp_path / dir_name / ".gitkeep"
        gitkeep_path.write_text("existing content")
        
        # Run the function
        create_gitkeep_files(tmp_path)
        
        # Verify content is unchanged
        assert gitkeep_path.read_text() == "existing content"


class TestFullSetupIntegration:
    """Integration tests for the complete setup process."""

    def test_full_setup_creates_complete_structure(self, tmp_path):
        """Verify that a full setup creates the complete expected structure."""
        from setup_project_structure import create_directory_structure, create_gitkeep_files
        
        create_directory_structure(tmp_path)
        create_gitkeep_files(tmp_path)
        
        # Check top-level directories
        assert (tmp_path / "data").exists()
        assert (tmp_path / "code").exists()
        assert (tmp_path / "tests").exists()
        assert (tmp_path / "results").exists()
        
        # Check data subdirectories
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "derived").exists()
        assert (tmp_path / "data" / "metadata").exists()
        
        # Check test subdirectories
        assert (tmp_path / "tests" / "unit").exists()
        assert (tmp_path / "tests" / "integration").exists()
        
        # Check code subdirectories
        assert (tmp_path / "code" / "utils").exists()
        assert (tmp_path / "code" / "report_assets").exists()

    def test_all_gitkeep_files_exist(self, tmp_path):
        """Verify that all directories have .gitkeep files after full setup."""
        from setup_project_structure import create_directory_structure, create_gitkeep_files
        
        create_directory_structure(tmp_path)
        create_gitkeep_files(tmp_path)
        
        expected_gitkeeps = [
            "data/raw/.gitkeep",
            "data/derived/.gitkeep",
            "code/.gitkeep",
            "tests/unit/.gitkeep",
            "tests/integration/.gitkeep",
            "results/.gitkeep",
            "data/metadata/.gitkeep",
            "figures/.gitkeep",
            "specs/.gitkeep",
            "docs/.gitkeep",
            "code/utils/.gitkeep",
            "code/report_assets/.gitkeep",
        ]
        
        for gitkeep in expected_gitkeeps:
            assert (tmp_path / gitkeep).exists(), f"Missing .gitkeep: {gitkeep}"
