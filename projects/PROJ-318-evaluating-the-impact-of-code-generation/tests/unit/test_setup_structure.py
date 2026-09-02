import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to add the code directory to the path to import setup_structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_structure import create_directories, create_gitkeep_files, verify_structure

class TestSetupStructure:
    def setup_method(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_create_directories(self):
        """Test that all required directories are created."""
        created = create_directories()
        assert len(created) == 9, f"Expected 9 directories, got {len(created)}"
        
        # Verify each directory exists
        required_dirs = [
            "code",
            "code/utils",
            "data/raw",
            "data/raw/repos",
            "data/processed",
            "tests/unit",
            "tests/integration",
            "state",
            "logs"
        ]
        
        for dir_path in required_dirs:
            full_path = Path(self.test_dir) / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"Path {full_path} is not a directory"

    def test_create_gitkeep_files(self):
        """Test that .gitkeep files are created in all directories."""
        # First create directories
        create_directories()
        
        # Then create gitkeep files
        created = create_gitkeep_files()
        assert len(created) == 9, f"Expected 9 .gitkeep files, got {len(created)}"
        
        # Verify each .gitkeep exists
        required_dirs = [
            "code",
            "code/utils",
            "data/raw",
            "data/raw/repos",
            "data/processed",
            "tests/unit",
            "tests/integration",
            "state",
            "logs"
        ]
        
        for dir_path in required_dirs:
            full_path = Path(self.test_dir) / dir_path / ".gitkeep"
            assert full_path.exists(), f".gitkeep file {full_path} was not created"
            assert full_path.is_file(), f"Path {full_path} is not a file"

    def test_verify_structure_success(self):
        """Test verify_structure returns True when structure is complete."""
        create_directories()
        create_gitkeep_files()
        assert verify_structure() is True

    def test_verify_structure_missing_directory(self):
        """Test verify_structure returns False when a directory is missing."""
        create_directories()
        create_gitkeep_files()
        
        # Remove a directory
        (Path(self.test_dir) / "code").rmdir()
        
        assert verify_structure() is False

    def test_verify_structure_missing_gitkeep(self):
        """Test verify_structure returns False when a .gitkeep is missing."""
        create_directories()
        create_gitkeep_files()
        
        # Remove a .gitkeep file
        (Path(self.test_dir) / "code" / ".gitkeep").unlink()
        
        assert verify_structure() is False

    def test_create_directories_idempotent(self):
        """Test that running create_directories multiple times doesn't fail."""
        created1 = create_directories()
        created2 = create_directories()
        # Should create 0 on second run since they already exist
        assert len(created2) == 0

    def test_create_gitkeep_files_idempotent(self):
        """Test that running create_gitkeep_files multiple times doesn't fail."""
        create_directories()
        created1 = create_gitkeep_files()
        created2 = create_gitkeep_files()
        # Should create 0 on second run since they already exist
        assert len(created2) == 0