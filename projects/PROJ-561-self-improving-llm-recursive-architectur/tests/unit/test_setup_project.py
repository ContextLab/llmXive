import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestSetupProject(unittest.TestCase):
    """Unit tests for setup_project.py and setup_verify.py"""

    def setUp(self):
        """Create a temporary directory for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_create_project_structure_creates_directories(self):
        """Test that create_project_structure creates all required directories"""
        from setup_project import create_project_structure
        
        result = create_project_structure()
        
        # Check that all directories were created
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration"
        ]
        
        for dir_path in required_dirs:
            full_path = Path(self.temp_dir) / dir_path
            self.assertTrue(full_path.exists(), f"Directory {dir_path} was not created")
            self.assertTrue(full_path.is_dir(), f"{dir_path} is not a directory")

    def test_create_project_structure_creates_init_files(self):
        """Test that create_project_structure creates __init__.py in all directories"""
        from setup_project import create_project_structure
        
        result = create_project_structure()
        
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration"
        ]
        
        for dir_path in required_dirs:
            full_path = Path(self.temp_dir) / dir_path / "__init__.py"
            self.assertTrue(full_path.exists(), f"__init__.py not created in {dir_path}")
            self.assertTrue(full_path.is_file(), f"{dir_path}/__init__.py is not a file")

    def test_verify_project_structure_passes_when_complete(self):
        """Test that verify_project_structure passes when all files exist"""
        from setup_project import create_project_structure
        from setup_verify import verify_project_structure
        
        # First create the structure
        create_project_structure()
        
        # Then verify it
        # This should not raise an exception
        try:
            verify_project_structure()
        except FileNotFoundError:
            self.fail("verify_project_structure raised FileNotFoundError when structure is complete")

    def test_verify_project_structure_fails_when_missing(self):
        """Test that verify_project_structure fails when directories are missing"""
        from setup_verify import verify_project_structure
        
        # Don't create any structure - verify should fail
        with self.assertRaises(FileNotFoundError):
            verify_project_structure()

    def test_verify_project_structure_fails_when_init_missing(self):
        """Test that verify_project_structure fails when __init__.py is missing"""
        from setup_project import create_project_structure
        from setup_verify import verify_project_structure
        
        # Create structure
        create_project_structure()
        
        # Remove one __init__.py
        missing_init = Path(self.temp_dir) / "code" / "__init__.py"
        missing_init.unlink()
        
        # Verify should fail
        with self.assertRaises(FileNotFoundError):
            verify_project_structure()

    def test_create_project_structure_idempotent(self):
        """Test that running create_project_structure multiple times is safe"""
        from setup_project import create_project_structure
        
        # Run twice
        result1 = create_project_structure()
        result2 = create_project_structure()
        
        # Both should succeed
        self.assertEqual(result1['total_directories'], result2['total_directories'])
        self.assertEqual(result1['total_init_files'], result2['total_init_files'])

if __name__ == '__main__':
    unittest.main()