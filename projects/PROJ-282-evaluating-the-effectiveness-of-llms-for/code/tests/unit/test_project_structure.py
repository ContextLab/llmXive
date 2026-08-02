import os
import pytest
from pathlib import Path
import tempfile
import shutil
from setup_project_structure import create_structure

class TestProjectStructure:
    """Tests for the project structure creation script."""

    def test_directory_structure_exists(self, tmp_path):
        """Verify that create_structure creates all required directories."""
        required_dirs = [
            "src",
            "tests",
            "data",
            "data/raw",
            "data/processed",
            "data/results",
            "data/logs",
            "state",
            "contracts",
            "figures",
        ]
        
        # Create structure in temp directory
        create_structure(str(tmp_path))
        
        # Verify all directories exist
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_nested_directories_created(self, tmp_path):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        create_structure(str(tmp_path))
        
        nested_dirs = [
            "data/raw",
            "data/processed",
            "data/results",
            "data/logs",
        ]
        
        for dir_name in nested_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Nested directory {dir_name} was not created"

    def test_idempotent_creation(self, tmp_path):
        """Verify that running create_structure twice doesn't cause errors."""
        # First run
        create_structure(str(tmp_path))
        
        # Second run should not raise errors
        create_structure(str(tmp_path))
        
        # Verify directories still exist
        assert (tmp_path / "src").exists()
        assert (tmp_path / "data/raw").exists()
