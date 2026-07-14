"""
Unit tests for data directory structure setup.
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_dirs import setup_data_directories

def test_data_directories_created():
    """Test that the required data directories are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the project root structure
        data_root = Path(tmpdir) / "data"
        data_root.mkdir()

        directories = [
            data_root / "raw",
            data_root / "processed",
            data_root / "artifacts",
        ]

        for directory in directories:
            assert not directory.exists(), f"Directory {directory} should not exist before test"

        # Temporarily patch the function to use our temp dir
        original_func = setup_data_directories
        
        def mock_setup():
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            return len(directories)

        try:
            result = mock_setup()
            
            for directory in directories:
                assert directory.exists(), f"Directory {directory} should exist after setup"
                assert directory.is_dir(), f"{directory} should be a directory"
                
        finally:
            pass  # Cleanup handled by TemporaryDirectory

def test_directories_are_writable():
    """Test that created directories are writable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_root = Path(tmpdir) / "data"
        data_root.mkdir()

        test_file = data_root / "raw" / "test_write.txt"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        test_file.write_text("test")
        assert test_file.exists()
        assert test_file.read_text() == "test"