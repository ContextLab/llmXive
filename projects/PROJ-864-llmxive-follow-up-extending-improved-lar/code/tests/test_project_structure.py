"""
Test project structure and directory organization.

This test ensures that all required directories and files exist
according to the project specification.
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure code root is in path
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

class TestProjectStructure(unittest.TestCase):
    """Test that the project structure is correctly set up."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.code_root = code_root
        cls.project_root = cls.code_root.parent
        
        # Define required directories
        cls.required_dirs = [
            "code",
            "code/data",
            "code/models",
            "code/training",
            "code/analysis",
            "code/utils",
            "code/tests",
        ]
        
        # Define required files
        cls.required_files = [
            "code/main.py",
            "code/requirements.txt",
        ]
    
    def test_required_directories_exist(self):
        """Test that all required directories exist."""
        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            self.assertTrue(
                full_path.exists() and full_path.is_dir(),
                f"Required directory does not exist: {full_path}"
            )
    
    def test_required_files_exist(self):
        """Test that all required files exist."""
        for file_path in self.required_files:
            full_path = self.project_root / file_path
            self.assertTrue(
                full_path.exists() and full_path.is_file(),
                f"Required file does not exist: {full_path}"
            )
    
    def test_tests_directory_is_not_empty(self):
        """Test that the tests directory contains at least __init__.py."""
        tests_dir = self.project_root / "code" / "tests"
        init_file = tests_dir / "__init__.py"
        self.assertTrue(
            init_file.exists() and init_file.is_file(),
            f"Tests directory missing __init__.py: {init_file}"
        )
    
    def test_code_directory_has_python_files(self):
        """Test that the code directory contains Python files."""
        python_files = list(self.code_root.glob("**/*.py"))
        self.assertGreater(
            len(python_files), 0,
            "No Python files found in the code directory"
        )

def run_tests():
    """Run all tests in this module."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestProjectStructure)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)