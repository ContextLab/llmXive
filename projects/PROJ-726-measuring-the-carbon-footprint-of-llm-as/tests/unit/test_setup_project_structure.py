import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project_structure import create_directory_structure


class TestCreateDirectoryStructure:
    """Tests for the create_directory_structure function."""

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            
            # Call the function
            create_directory_structure(root)
            
            # Verify directories exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/outputs",
                "tests",
                "output",
            ]
            
            for dir_name in required_dirs:
                dir_path = root / dir_name
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_creates_nested_directories(self):
        """Verify that nested directories (like data/raw) are created correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            
            create_directory_structure(root)
            
            # Verify nested structure
            data_raw = root / "data" / "raw"
            data_processed = root / "data" / "processed"
            data_outputs = root / "data" / "outputs"
            
            assert data_raw.exists() and data_raw.is_dir()
            assert data_processed.exists() and data_processed.is_dir()
            assert data_outputs.exists() and data_outputs.is_dir()

    def test_idempotent_when_directories_exist(self):
        """Verify that running the function again doesn't fail if directories exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            
            # Create directories first
            create_directory_structure(root)
            
            # Run again - should not raise an exception
            create_directory_structure(root)
            
            # Verify directories still exist
            required_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/outputs",
                "tests",
                "output",
            ]
            
            for dir_name in required_dirs:
                dir_path = root / dir_name
                assert dir_path.exists()

    def test_creates_parent_directories(self):
        """Verify that parent directories are created for nested paths."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            
            # Remove data directory to test parent creation
            if (root / "data").exists():
                (root / "data").rmdir()
            
            create_directory_structure(root)
            
            # Verify data and its subdirectories exist
            assert (root / "data").exists()
            assert (root / "data" / "raw").exists()
            assert (root / "data" / "processed").exists()
            assert (root / "data" / "outputs").exists()