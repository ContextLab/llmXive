import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
from setup_structure import create_project_structure

class TestProjectStructure:
    """Tests for the project structure creation functionality."""

    def test_creates_all_required_directories(self):
        """Verify that all required subdirectories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir) / "test_project"
            create_project_structure(str(base_path))
            
            required_dirs = [
                "data/raw",
                "data/processed",
                "results",
                "code",
                "tests"
            ]
            
            for dir_path in required_dirs:
                full_path = base_path / dir_path
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_handles_existing_directories(self):
        """Verify that existing directories are not overwritten or cause errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir) / "test_project"
            
            # Create the structure first time
            create_project_structure(str(base_path))
            
            # Create it again - should not raise errors
            create_project_structure(str(base_path))
            
            # Verify directories still exist
            assert (base_path / "data/raw").exists()
            assert (base_path / "results").exists()

    def test_creates_parent_directories(self):
        """Verify that parent directories are created if they don't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Use a nested path where parent doesn't exist
            base_path = Path(tmp_dir) / "nested" / "deep" / "test_project"
            create_project_structure(str(base_path))
            
            assert base_path.exists()
            assert (base_path / "data/raw").exists()

    def test_directory_permissions(self):
        """Verify that created directories are writable."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir) / "test_project"
            create_project_structure(str(base_path))
            
            # Try to create a file in each directory
            test_file_content = b"test"
            
            # data/raw
            test_file = base_path / "data/raw" / "test.txt"
            test_file.write_bytes(test_file_content)
            assert test_file.exists()
            test_file.unlink()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
