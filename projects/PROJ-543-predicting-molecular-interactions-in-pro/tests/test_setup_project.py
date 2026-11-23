"""
Unit tests for the project setup script.
Verifies that the required directory structure is created.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Import the setup logic
# We need to make sure the code directory is in the path if we import directly,
# but since setup_project.py is in code/, we might need to adjust sys.path or import differently.
# For this test, we will import the function logic directly if possible, or mock the execution.
# However, the script is a standalone runner. Let's test the logic by importing the module.

# Add the parent directory of 'code' to the path if 'tests' is in the root and 'code' is sibling
# Actually, the script is in code/setup_project.py. We need to import it.
# Let's assume we run this test from the project root.
import sys
from pathlib import Path

# Ensure code/ is in path
current_dir = Path(__file__).parent
project_root = current_dir.parent
code_dir = project_root / "code"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import main

class TestProjectSetup(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        self.expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/results",
            "tests",
            "specs"
        ]

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_directories_created(self):
        """Test that all required directories are created."""
        # Run the setup logic
        main()
        
        for dir_name in self.expected_dirs:
            dir_path = os.path.join(self.test_dir, dir_name)
            self.assertTrue(os.path.exists(dir_path), f"Directory {dir_name} was not created.")
            self.assertTrue(os.path.isdir(dir_path), f"{dir_name} exists but is not a directory.")

    def test_nested_directories_created(self):
        """Test that nested directories like data/raw are created."""
        main()
        
        nested_dirs = [
            "data/raw",
            "data/processed",
            "data/results"
        ]
        
        for dir_name in nested_dirs:
            dir_path = os.path.join(self.test_dir, dir_name)
            self.assertTrue(os.path.exists(dir_path), f"Nested directory {dir_name} was not created.")

if __name__ == '__main__':
    unittest.main()