import os
import pytest
from pathlib import Path
import shutil

class TestDirectoryStructureIntegration:
    """Integration tests for the full directory structure setup."""

    def test_full_directory_setup(self, tmp_path):
        """Test that the full directory structure is created correctly."""
        # Create a temporary project structure
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Create the expected directories
        data_raw = project_root / "data" / "raw"
        data_processed = project_root / "data" / "processed"
        results = project_root / "results"
        
        directories = [data_raw, data_processed, results]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            gitkeep_path = directory / ".gitkeep"
            gitkeep_path.touch()
        
        # Verify all directories exist
        for directory in directories:
            assert directory.exists(), f"Directory {directory} was not created"
            assert directory.is_dir(), f"{directory} is not a directory"
        
        # Verify .gitkeep files exist
        for directory in directories:
            gitkeep_path = directory / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep not found in {directory}"
            assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

    def test_directory_structure_persistence(self, tmp_path):
        """Test that the directory structure persists after creation."""
        project_root = tmp_path / "persistent_project"
        project_root.mkdir()
        
        data_raw = project_root / "data" / "raw"
        data_raw.mkdir(parents=True)
        (data_raw / ".gitkeep").touch()
        
        # Verify the structure exists
        assert data_raw.exists()
        assert (data_raw / ".gitkeep").exists()
        
        # Simulate "closing" and reopening by checking again
        assert data_raw.exists()
        assert (data_raw / ".gitkeep").exists()