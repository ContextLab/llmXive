"""
Unit test for T001: Verify project structure creation.
Tests that the setup script creates the correct directory structure and __init__.py files.
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_project import create_project_structure, DIRECTORIES

class TestProjectStructureCreation(unittest.TestCase):
    """Test cases for project structure creation."""

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock ROOT_DIR to point to our temp directory
        self.root_dir = Path(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('setup_project.ROOT_DIR')
    def test_create_project_structure_creates_directories(self, mock_root_dir):
        """Test that create_project_structure creates all required directories."""
        mock_root_dir = self.root_dir
        
        # Run the setup function
        create_project_structure()
        
        # Verify all directories were created
        for dir_name in DIRECTORIES:
            dir_path = self.root_dir / dir_name
            self.assertTrue(dir_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(dir_path.is_dir(), f"{dir_path} is not a directory")

    @patch('setup_project.ROOT_DIR')
    def test_create_project_structure_creates_init_files(self, mock_root_dir):
        """Test that create_project_structure creates __init__.py in all directories."""
        mock_root_dir = self.root_dir
        
        # Run the setup function
        create_project_structure()
        
        # Verify __init__.py files were created
        for dir_name in DIRECTORIES:
            dir_path = self.root_dir / dir_name
            init_file = dir_path / "__init__.py"
            self.assertTrue(init_file.exists(), f"__init__.py not created in {dir_path}")
            self.assertTrue(init_file.is_file(), f"{init_file} is not a file")

    @patch('setup_project.ROOT_DIR')
    def test_create_project_structure_idempotent(self, mock_root_dir):
        """Test that running create_project_structure multiple times is safe."""
        mock_root_dir = self.root_dir
        
        # Run the setup function twice
        create_project_structure()
        create_project_structure()
        
        # Verify all directories and files still exist
        for dir_name in DIRECTORIES:
            dir_path = self.root_dir / dir_name
            self.assertTrue(dir_path.exists(), f"Directory {dir_path} missing after second run")
            init_file = dir_path / "__init__.py"
            self.assertTrue(init_file.exists(), f"__init__.py missing after second run in {dir_path}")

if __name__ == '__main__':
    unittest.main()