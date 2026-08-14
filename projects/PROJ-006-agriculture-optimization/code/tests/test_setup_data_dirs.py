"""
Tests for the setup_data_dirs.py script.
Verifies that the required directories are created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from scripts.setup_data_dirs import ensure_dir, main


class TestSetupDataDirs:
    """Test suite for data directory setup."""

    def test_ensure_dir_creates_new_directory(self, tmp_path):
        """Test that ensure_dir creates a new directory."""
        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()
        ensure_dir(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_dir_skips_existing_directory(self, tmp_path):
        """Test that ensure_dir does not modify existing directory."""
        existing_dir = tmp_path / "existing_directory"
        existing_dir.mkdir()
        original_mtime = existing_dir.stat().st_mtime

        ensure_dir(existing_dir)

        assert existing_dir.exists()
        assert existing_dir.is_dir()
        # Directory should not be recreated (mtime should be same or very close)
        assert existing_dir.stat().st_mtime >= original_mtime

    def test_main_creates_required_directories(self, tmp_path):
        """Test that main() creates the required data directories."""
        # Create a temporary directory structure to mimic project root
        data_root = tmp_path / "data"
        data_root.mkdir()

        # Mock the script location to point to our temp directory
        import scripts.setup_data_dirs as module
        original_resolve = Path.resolve
        
        def mock_resolve(self):
            if str(self) == str(Path(__file__)):
                return tmp_path / "scripts" / "setup_data_dirs.py"
            return original_resolve(self)
        
        # Temporarily patch Path.resolve
        Path.resolve = mock_resolve

        try:
            # Run main
            result = main()
            
            # Verify return code
            assert result == 0
            
            # Verify directories were created
            raw_dir = tmp_path / "data" / "raw"
            processed_dir = tmp_path / "data" / "processed"
            logs_dir = tmp_path / "data" / "logs"
            
            assert raw_dir.exists()
            assert processed_dir.exists()
            assert logs_dir.exists()
            assert raw_dir.is_dir()
            assert processed_dir.is_dir()
            assert logs_dir.is_dir()
        finally:
            # Restore original resolve
            Path.resolve = original_resolve

    def test_main_creates_nested_directories(self, tmp_path):
        """Test that main() creates nested directory structures."""
        import scripts.setup_data_dirs as module
        original_resolve = Path.resolve
        
        def mock_resolve(self):
            if str(self) == str(Path(__file__)):
                return tmp_path / "scripts" / "setup_data_dirs.py"
            return original_resolve(self)
        
        Path.resolve = mock_resolve

        try:
            result = main()
            assert result == 0
            
            # Check that all required subdirectories exist
            data_raw = tmp_path / "data" / "raw"
            data_processed = tmp_path / "data" / "processed"
            data_logs = tmp_path / "data" / "logs"
            
            assert data_raw.exists()
            assert data_processed.exists()
            assert data_logs.exists()
        finally:
            Path.resolve = original_resolve

    def test_directories_are_writable(self, tmp_path):
        """Test that created directories are writable."""
        import scripts.setup_data_dirs as module
        original_resolve = Path.resolve
        
        def mock_resolve(self):
            if str(self) == str(Path(__file__)):
                return tmp_path / "scripts" / "setup_data_dirs.py"
            return original_resolve(self)
        
        Path.resolve = mock_resolve

        try:
            main()
            
            # Try to write a test file to each directory
            test_content = b"test content"
            
            raw_file = tmp_path / "data" / "raw" / "test.txt"
            processed_file = tmp_path / "data" / "processed" / "test.txt"
            logs_file = tmp_path / "data" / "logs" / "test.txt"
            
            raw_file.write_bytes(test_content)
            processed_file.write_bytes(test_content)
            logs_file.write_bytes(test_content)
            
            # Verify files were written
            assert raw_file.read_bytes() == test_content
            assert processed_file.read_bytes() == test_content
            assert logs_file.read_bytes() == test_content
        finally:
            Path.resolve = original_resolve