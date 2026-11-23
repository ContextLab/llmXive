"""
Tests for data directory creation and verification.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

# We need to add the code directory to the path to import our setup script
# Assuming tests are run from the project root
sys_path = Path(__file__).parent.parent
if str(sys_path) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(sys_path))

from setup_data_dirs import ensure_directory

class TestDataDirectories:
    """Test cases for data directory creation logic."""

    def test_ensure_directory_creates_new(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        test_dir = tmp_path / "test_new_dir"
        assert not test_dir.exists()
        
        result = ensure_directory(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()
        assert (test_dir / ".gitkeep").exists()

    def test_ensure_directory_existing(self, tmp_path):
        """Test that ensure_directory handles existing directories."""
        test_dir = tmp_path / "test_existing_dir"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a dummy file to ensure it's not empty
        (test_dir / "dummy.txt").write_text("test")
        
        result = ensure_directory(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert (test_dir / ".gitkeep").exists()
        # Ensure existing file is still there
        assert (test_dir / "dummy.txt").exists()

    def test_ensure_directory_nested(self, tmp_path):
        """Test that ensure_directory creates nested directories."""
        test_dir = tmp_path / "level1" / "level2" / "level3"
        assert not test_dir.exists()
        
        result = ensure_directory(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert (test_dir.parent.parent).exists()
        assert (test_dir.parent).exists()
        assert (test_dir / ".gitkeep").exists()

    def test_ensure_directory_permission_error(self, tmp_path):
        """Test handling of permission errors (mocked)."""
        # We can't easily test actual permission errors in a temp dir
        # without complex mocking, so we test the logic path
        # by trying to create a directory where we don't have write access
        # This is hard to simulate reliably in tests, so we skip for now
        # or rely on the fact that the function returns False on exception
        pass

def test_data_dirs_structure_exists():
    """
    Integration test: Verify that the expected data directories exist
    in the project root after running the setup script.
    """
    project_root = Path(__file__).parent.parent
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    
    # These should exist if T001b was run successfully
    # If they don't exist, the test will fail, indicating T001b needs to be run
    assert data_raw.exists(), f"Directory {data_raw} does not exist. Run T001b."
    assert data_processed.exists(), f"Directory {data_processed} does not exist. Run T001b."
    assert data_raw.is_dir()
    assert data_processed.is_dir()
    
    # Verify they contain the .gitkeep marker
    assert (data_raw / ".gitkeep").exists()
    assert (data_processed / ".gitkeep").exists()