"""
Test module for T001b: Directory and Placeholder Creation.
Verifies that the required project structure and .gitkeep files exist.
"""
import os
import sys
import unittest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestDirectoryStructure(unittest.TestCase):
    
    def test_code_directory_exists(self):
        """Verify code/ directory exists."""
        path = os.path.join(project_root, "code")
        self.assertTrue(os.path.isdir(path), f"Directory {path} does not exist")

    def test_data_directory_exists(self):
        """Verify data/ directory exists."""
        path = os.path.join(project_root, "data")
        self.assertTrue(os.path.isdir(path), f"Directory {path} does not exist")

    def test_tests_directory_exists(self):
        """Verify tests/ directory exists."""
        path = os.path.join(project_root, "tests")
        self.assertTrue(os.path.isdir(path), f"Directory {path} does not exist")

    def test_data_raw_directory_exists(self):
        """Verify data/raw/ directory exists."""
        path = os.path.join(project_root, "data", "raw")
        self.assertTrue(os.path.isdir(path), f"Directory {path} does not exist")

    def test_data_generated_directory_exists(self):
        """Verify data/generated/ directory exists."""
        path = os.path.join(project_root, "data", "generated")
        self.assertTrue(os.path.isdir(path), f"Directory {path} does not exist")

    def test_data_results_directory_exists(self):
        """Verify data/results/ directory exists."""
        path = os.path.join(project_root, "data", "results")
        self.assertTrue(os.path.isdir(path), f"Directory {path} does not exist")

    def test_gitkeep_in_data_raw(self):
        """Verify .gitkeep exists in data/raw/."""
        path = os.path.join(project_root, "data", "raw", ".gitkeep")
        self.assertTrue(os.path.isfile(path), f"File {path} does not exist")

    def test_gitkeep_in_data_generated(self):
        """Verify .gitkeep exists in data/generated/."""
        path = os.path.join(project_root, "data", "generated", ".gitkeep")
        self.assertTrue(os.path.isfile(path), f"File {path} does not exist")

    def test_gitkeep_in_data_results(self):
        """Verify .gitkeep exists in data/results/."""
        path = os.path.join(project_root, "data", "results", ".gitkeep")
        self.assertTrue(os.path.isfile(path), f"File {path} does not exist")

    def test_code_init_exists(self):
        """Verify code/__init__.py exists."""
        path = os.path.join(project_root, "code", "__init__.py")
        self.assertTrue(os.path.isfile(path), f"File {path} does not exist")

    def test_tests_init_exists(self):
        """Verify tests/__init__.py exists."""
        path = os.path.join(project_root, "tests", "__init__.py")
        self.assertTrue(os.path.isfile(path), f"File {path} does not exist")

if __name__ == "__main__":
    unittest.main()