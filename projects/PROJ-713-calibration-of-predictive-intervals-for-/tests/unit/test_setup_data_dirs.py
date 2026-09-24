"""
Unit tests for setup_data_dirs.py (T001c verification).
Verifies that data/raw/ directory is created and writable.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_data_dirs import ensure_dir, setup_data_directories

class TestEnsureDir:
    """Tests for the ensure_dir function."""

    def test_existing_directory(self, tmp_path):
        """Test that existing directory returns True."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        
        result = ensure_dir(test_dir)
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_new_directory_creation(self, tmp_path):
        """Test that new directory is created successfully."""
        test_dir = tmp_path / "new_dir"
        
        assert not test_dir.exists()
        result = ensure_dir(test_dir)
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_nested_directory_creation(self, tmp_path):
        """Test that nested directories are created with parents=True."""
        test_dir = tmp_path / "level1" / "level2" / "level3"
        
        assert not test_dir.exists()
        result = ensure_dir(test_dir)
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_unwritable_directory(self, tmp_path):
        """Test behavior when directory cannot be written (permission error)."""
        # Create a directory and make it read-only
        test_dir = tmp_path / "readonly"
        test_dir.mkdir()
        os.chmod(test_dir, 0o444)  # Read-only
        
        try:
            # This should fail to create a subdirectory or write a test file
            # Note: On some systems (e.g., root), this might still succeed
            # The test is primarily to ensure the logic handles the error path
            result = ensure_dir(test_dir / "subdir")
            # If we can't write, ensure_dir should return False
            # If we are root, it might succeed, so we check the result
            if os.geteuid() == 0:
                # Root user can write anywhere
                assert result is True
            else:
                assert result is False
        finally:
            # Restore permissions for cleanup
            os.chmod(test_dir, 0o755)

class TestSetupDataDirectories:
    """Tests for the main setup function."""

    def test_data_raw_creation(self, tmp_path, monkeypatch):
        """Test that setup_data_directories creates data/raw/."""
        # Monkeypatch PROJECT_ROOT to use tmp_path
        # We need to patch the module-level variable
        import setup_data_dirs
        original_root = setup_data_dirs.PROJECT_ROOT
        setup_data_dirs.PROJECT_ROOT = tmp_path
        
        try:
            result = setup_data_directories()
            raw_dir = tmp_path / "data" / "raw"
            
            assert result is True
            assert raw_dir.exists()
            assert raw_dir.is_dir()
            
            # Verify writability
            test_file = raw_dir / "test_write.txt"
            test_file.write_text("test")
            assert test_file.exists()
            test_file.unlink()
        finally:
            setup_data_dirs.PROJECT_ROOT = original_root

    def test_writable_verification(self, tmp_path, monkeypatch):
        """Test that the created directory is actually writable."""
        import setup_data_dirs
        original_root = setup_data_dirs.PROJECT_ROOT
        setup_data_dirs.PROJECT_ROOT = tmp_path
        
        try:
            setup_data_directories()
            raw_dir = tmp_path / "data" / "raw"
            
            # Attempt to write a file
            test_file = raw_dir / "verification.txt"
            test_file.write_text("verification content")
            assert test_file.read_text() == "verification content"
            test_file.unlink()
        finally:
            setup_data_dirs.PROJECT_ROOT = original_root