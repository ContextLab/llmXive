"""
Unit tests for project structure initialization.
Verifies that directories and .gitkeep files are created correctly.
"""
import os
import tempfile
import shutil
import pytest
from code.setup_project_structure import create_directory_structure, create_gitkeep_files

class TestProjectStructure:
    def setup_method(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)

    def teardown_method(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)

    def test_create_directory_structure(self):
        """Test that core directories are created."""
        create_directory_structure(".")
        
        required_dirs = ["code", "data", "tests"]
        for dir_name in required_dirs:
            path = os.path.join(self.test_dir, dir_name)
            assert os.path.isdir(path), f"Directory {dir_name} was not created"

    def test_create_gitkeep_files(self):
        """Test that .gitkeep files are created in data subdirectories."""
        # First ensure directories exist
        create_directory_structure(".")
        create_gitkeep_files(".")
        
        required_gitkeeps = [
            "data/raw/.gitkeep",
            "data/generated/.gitkeep",
            "data/results/.gitkeep",
        ]
        
        for gitkeep in required_gitkeeps:
            path = os.path.join(self.test_dir, gitkeep)
            assert os.path.isfile(path), f".gitkeep file {gitkeep} was not created"

    def test_idempotency(self):
        """Test that running the script twice doesn't fail."""
        create_directory_structure(".")
        create_gitkeep_files(".")
        
        # Run again
        create_directory_structure(".")
        create_gitkeep_files(".")
        
        # Verify files still exist
        assert os.path.isdir(os.path.join(self.test_dir, "code"))
        assert os.path.isfile(os.path.join(self.test_dir, "data/raw/.gitkeep"))