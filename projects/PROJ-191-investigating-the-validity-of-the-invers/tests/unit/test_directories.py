import pytest
from pathlib import Path
import tempfile
import shutil
import os

from code.utils.directories import ensure_data_directories

class TestEnsureDataDirectories:
    """Unit tests for the ensure_data_directories function (T007)."""

    def test_creates_missing_directories(self, tmp_path: Path):
        """Test that the function creates directories that do not exist."""
        # tmp_path is a fresh temporary directory
        expected_dirs = [
            tmp_path / "data" / "raw",
            tmp_path / "data" / "processed",
            tmp_path / "data" / "results"
        ]
        
        # Verify they don't exist yet
        for d in expected_dirs:
            assert not d.exists()
        
        # Run the function
        result = ensure_data_directories(tmp_path)
        
        # Verify they now exist
        for d in expected_dirs:
            assert d.exists()
            assert d.is_dir()
        
        # Verify returned paths match expected
        assert len(result) == 3
        assert result == expected_dirs

    def test_skips_existing_directories(self, tmp_path: Path):
        """Test that the function handles existing directories gracefully."""
        # Pre-create one of the directories
        pre_created = tmp_path / "data" / "raw"
        pre_created.mkdir(parents=True)
        
        # Run the function
        result = ensure_data_directories(tmp_path)
        
        # Verify all exist
        assert all(d.exists() for d in result)
        assert len(result) == 3

    def test_raises_on_permission_error(self, tmp_path: Path):
        """Test that the function raises RuntimeError on permission errors."""
        # Create a file where we expect a directory to be
        # This simulates a conflict that might arise in edge cases or permissions
        # Note: Simulating actual permission denied is hard in temp dirs without root
        # So we test the logic path where a path exists but is not a directory
        conflict_path = tmp_path / "data" / "raw"
        conflict_path.mkdir(parents=True)
        
        # Now create a file with the same name as a parent of a required dir? 
        # Actually, let's test the specific check: if path exists but is not a dir
        # We need to force a scenario where a required subpath is a file.
        # e.g. data/raw is a file.
        file_path = tmp_path / "data" / "raw"
        file_path.mkdir(parents=True) # Make data/raw a dir first
        file_path.rmdir() # Remove it
        file_path.touch() # Make it a file
        
        # Now try to create data/raw/processed (which would be inside a file)
        # But our function tries to create data/raw, data/processed, data/results
        # If data/raw is a file, ensure_data_directories should fail when trying to
        # access it or create children? 
        # Actually, the function checks `if not full_path.exists()` -> creates.
        # If it exists, it checks `if not full_path.is_dir()`.
        
        # Let's set up: tmp_path/data/raw is a FILE
        file_path = tmp_path / "data" / "raw"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.touch()
        
        with pytest.raises(RuntimeError, match="not a directory"):
            ensure_data_directories(tmp_path)

    def test_nested_structure_creation(self, tmp_path: Path):
        """Test that parent directories are created if missing (parents=True)."""
        # Ensure only the root exists
        assert tmp_path.exists()
        
        result = ensure_data_directories(tmp_path)
        
        # Verify the full nested structure
        for d in result:
            assert d.exists()
            # Verify parent also exists
            assert d.parent.exists()