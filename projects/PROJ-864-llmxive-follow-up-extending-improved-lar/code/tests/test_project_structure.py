"""
Test suite for verifying project directory structure and file existence.

Ensures that all required directories and files exist as specified in the project plan.
"""
import os
import sys
import unittest
from pathlib import Path

# Ensure imports work
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.config import get_project_root, get_data_dir, get_raw_dir, get_processed_dir, get_artifacts_dir


class TestProjectStructure(unittest.TestCase):
    """Test cases for project structure validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = get_project_root()
        self.code_dir = self.project_root / "code"
        self.data_dir = get_data_dir()
        self.raw_dir = get_raw_dir()
        self.processed_dir = get_processed_dir()
        self.artifacts_dir = get_artifacts_dir()

    def test_code_directory_exists(self):
        """Verify that the code directory exists."""
        self.assertTrue(self.code_dir.exists(), f"Code directory not found: {self.code_dir}")
        self.assertTrue(self.code_dir.is_dir(), f"Code path is not a directory: {self.code_dir}")

    def test_data_directory_exists(self):
        """Verify that the data directory exists."""
        self.assertTrue(self.data_dir.exists(), f"Data directory not found: {self.data_dir}")
        self.assertTrue(self.data_dir.is_dir(), f"Data path is not a directory: {self.data_dir}")

    def test_raw_directory_exists(self):
        """Verify that the raw data directory exists."""
        self.assertTrue(self.raw_dir.exists(), f"Raw data directory not found: {self.raw_dir}")
        self.assertTrue(self.raw_dir.is_dir(), f"Raw data path is not a directory: {self.raw_dir}")

    def test_processed_directory_exists(self):
        """Verify that the processed data directory exists."""
        self.assertTrue(self.processed_dir.exists(), f"Processed data directory not found: {self.processed_dir}")
        self.assertTrue(self.processed_dir.is_dir(), f"Processed data path is not a directory: {self.processed_dir}")

    def test_artifacts_directory_exists(self):
        """Verify that the artifacts directory exists."""
        self.assertTrue(self.artifacts_dir.exists(), f"Artifacts directory not found: {self.artifacts_dir}")
        self.assertTrue(self.artifacts_dir.is_dir(), f"Artifacts path is not a directory: {self.artifacts_dir}")

    def test_tests_directory_exists(self):
        """Verify that the tests directory exists."""
        tests_dir = self.code_dir / "tests"
        self.assertTrue(tests_dir.exists(), f"Tests directory not found: {tests_dir}")
        self.assertTrue(tests_dir.is_dir(), f"Tests path is not a directory: {tests_dir}")

    def test_main_py_exists(self):
        """Verify that main.py exists in the code directory."""
        main_py = self.code_dir / "main.py"
        self.assertTrue(main_py.exists(), f"main.py not found: {main_py}")
        self.assertTrue(main_py.is_file(), f"main.py is not a file: {main_py}")

    def test_requirements_txt_exists(self):
        """Verify that requirements.txt exists in the project root."""
        requirements = self.project_root / "requirements.txt"
        self.assertTrue(requirements.exists(), f"requirements.txt not found: {requirements}")
        self.assertTrue(requirements.is_file(), f"requirements.txt is not a file: {requirements}")


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
