import os
import pytest
from pathlib import Path
from setup.create_structure import create_structure

class TestCreateStructure:
    """Tests for the project structure creation task T001a."""

    def test_creates_root_directories(self, tmp_path, monkeypatch):
        """Verify that create_structure creates the required root directories."""
        # Change to temp directory to avoid polluting the actual project root
        monkeypatch.chdir(tmp_path)
        
        # Run the function
        created = create_structure()
        
        # Verify directories were created
        expected_dirs = {"code", "data", "tests", "state", "results", "contracts"}
        created_dirs = {Path(d).name for d in created}
        
        assert expected_dirs == created_dirs, f"Expected {expected_dirs}, got {created_dirs}"
        
        # Verify they actually exist on disk
        for dir_name in expected_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_handles_existing_directories(self, tmp_path, monkeypatch):
        """Verify that create_structure doesn't fail if directories already exist."""
        monkeypatch.chdir(tmp_path)
        
        # Pre-create one directory
        (tmp_path / "code").mkdir()
        
        # Run the function - should not raise
        created = create_structure()
        
        # Should report that 'code' already exists
        assert len(created) == 5, "Should only create 5 new directories"

    def test_creates_empty_directories(self, tmp_path, monkeypatch):
        """Verify that the created directories are empty (no files)."""
        monkeypatch.chdir(tmp_path)
        
        create_structure()
        
        for dir_name in ["code", "data", "tests", "state", "results", "contracts"]:
            dir_path = tmp_path / dir_name
            files = list(dir_path.iterdir())
            assert len(files) == 0, f"Directory {dir_path} should be empty after creation"