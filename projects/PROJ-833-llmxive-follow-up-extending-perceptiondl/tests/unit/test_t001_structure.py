"""
Unit test for Task T001: Verify project structure creation.

This test ensures that the required directory hierarchy was created
correctly by the setup_structure.py script.
"""
import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path to allow imports if needed, 
# though this test primarily checks filesystem state.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

class TestT001Structure(unittest.TestCase):
    """Test cases for verifying the project directory structure."""

    def setUp(self):
        """Determine the project root path."""
        # Assuming the test is run from the project root or similar context
        # We look for the specific project directory relative to the test file
        test_file_dir = Path(__file__).resolve().parent
        repo_root = test_file_dir.parent.parent
        
        self.project_name = "PROJ-833-llmxive-follow-up-extending-perceptiondl"
        self.base_path = repo_root / "projects" / self.project_name

    def test_base_path_exists(self):
        """Verify the main project directory exists."""
        self.assertTrue(self.base_path.exists(), f"Base path {self.base_path} does not exist")
        self.assertTrue(self.base_path.is_dir(), f"Base path {self.base_path} is not a directory")

    def test_code_directories(self):
        """Verify all code subdirectories exist."""
        code_dirs = ["synthetic", "models", "metrics", "analysis"]
        for d in code_dirs:
            dir_path = self.base_path / "code" / d
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Missing code directory: {dir_path}"
            )

    def test_test_directories(self):
        """Verify all test subdirectories exist."""
        test_dirs = ["unit", "contract"]
        for d in test_dirs:
            dir_path = self.base_path / "tests" / d
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Missing test directory: {dir_path}"
            )

    def test_data_directories(self):
        """Verify all data subdirectories exist."""
        data_dirs = ["raw", "synthetic", "processed"]
        for d in data_dirs:
            dir_path = self.base_path / "data" / d
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Missing data directory: {dir_path}"
            )

    def test_state_directory(self):
        """Verify the state directory exists."""
        state_path = self.base_path / "state"
        self.assertTrue(
            state_path.exists() and state_path.is_dir(),
            f"Missing state directory: {state_path}"
        )

if __name__ == "__main__":
    unittest.main()