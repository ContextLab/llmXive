"""
Unit tests for project structure setup (Task T001).
"""
import unittest
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path to import setup scripts if needed, 
# though we will mostly verify filesystem state.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_project import create_project_structure
from setup_verify import verify_project_structure

class TestProjectStructure(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)
    
    def test_create_project_structure_creates_directories(self):
        """Test that create_project_structure creates all required directories."""
        create_project_structure()
        
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
        
        for dir_path_str in required_dirs:
            full_path = Path(self.temp_dir) / dir_path_str
            self.assertTrue(full_path.is_dir(), f"Directory {full_path} was not created")
    
    def test_create_project_structure_creates_init_files(self):
        """Test that create_project_structure creates __init__.py files."""
        create_project_structure()
        
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
        
        for dir_path_str in required_dirs:
            full_path = Path(self.temp_dir) / dir_path_str
            init_file = full_path / "__init__.py"
            self.assertTrue(init_file.exists(), f"__init__.py missing in {full_path}")
    
    def test_verify_project_structure_passes(self):
        """Test that verify_project_structure returns True after creation."""
        create_project_structure()
        # Re-run verify in the temp directory context
        # We need to temporarily change cwd or pass the path. 
        # The function uses Path.cwd(), so we rely on the setUp chdir.
        result = verify_project_structure()
        self.assertTrue(result, "Verification should pass after structure creation")
    
    def test_verify_project_structure_fails_on_missing(self):
        """Test that verify_project_structure returns False if structure is incomplete."""
        # Create only one directory
        Path(self.temp_dir, "code").mkdir()
        # Do not create __init__.py
        
        # Manually check logic since verify_project_structure uses cwd
        # We rely on the function's internal logic
        # But to test failure, we can just check the return value
        # Note: The function prints to stdout, which is fine for a unit test context
        result = verify_project_structure()
        self.assertFalse(result, "Verification should fail if structure is incomplete")

if __name__ == '__main__':
    unittest.main()