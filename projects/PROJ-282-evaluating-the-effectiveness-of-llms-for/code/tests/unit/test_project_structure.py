import os
import pytest
from pathlib import Path
import tempfile
import shutil
from setup_project_structure import create_structure

class TestProjectStructure:
    """Tests for the project structure creation functionality."""

    def test_directory_structure_exists(self, tmp_path):
        """Test that all required directories are created."""
        # Create structure in temporary directory
        success = create_structure(str(tmp_path))
        assert success is True

        # Verify all required directories exist
        required_dirs = [
            "src",
            "tests",
            "data/raw",
            "data/processed",
            "data/results",
            "state"
        ]

        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_gitkeep_files_created(self, tmp_path):
        """Test that .gitkeep files are created in all directories."""
        create_structure(str(tmp_path))

        required_dirs = [
            "src",
            "tests",
            "data/raw",
            "data/processed",
            "data/results",
            "state"
        ]

        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            gitkeep_path = dir_path / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep not found in {dir_name}"

    def test_nested_directories_created(self, tmp_path):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        create_structure(str(tmp_path))

        # Check that nested structure is preserved
        data_raw = tmp_path / "data" / "raw"
        data_processed = tmp_path / "data" / "processed"
        data_results = tmp_path / "data" / "results"

        assert data_raw.exists()
        assert data_processed.exists()
        assert data_results.exists()

    def test_idempotent_creation(self, tmp_path):
        """Test that running create_structure multiple times doesn't cause errors."""
        # Run twice
        success1 = create_structure(str(tmp_path))
        success2 = create_structure(str(tmp_path))

        assert success1 is True
        assert success2 is True

        # Verify directories still exist
        required_dirs = [
            "src",
            "tests",
            "data/raw",
            "data/processed",
            "data/results",
            "state"
        ]

        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists()

    def test_custom_root_path(self, tmp_path):
        """Test that structure can be created in a custom path."""
        custom_path = tmp_path / "custom_project"
        success = create_structure(str(custom_path))

        assert success is True
        assert custom_path.exists()
        assert (custom_path / "src").exists()
        assert (custom_path / "data").exists()