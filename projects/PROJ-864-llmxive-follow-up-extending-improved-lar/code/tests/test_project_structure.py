import os
import sys
import unittest
from pathlib import Path
from utils.config import get_project_root, get_data_dir, get_raw_dir, get_processed_dir, get_artifacts_dir

class TestProjectStructure(unittest.TestCase):
    """Test that project directories are correctly structured."""

    def test_project_root_exists(self):
        """Test that project root is accessible."""
        root = get_project_root()
        self.assertTrue(root.exists(), f"Project root does not exist: {root}")

    def test_code_dir_exists(self):
        """Test that code directory exists."""
        root = get_project_root()
        code_dir = root / "code"
        self.assertTrue(code_dir.exists(), f"Code directory does not exist: {code_dir}")

    def test_data_dir_exists(self):
        """Test that data directory exists."""
        data_dir = get_data_dir()
        self.assertTrue(data_dir.exists(), f"Data directory does not exist: {data_dir}")

    def test_raw_dir_exists(self):
        """Test that raw data directory exists."""
        raw_dir = get_raw_dir()
        self.assertTrue(raw_dir.exists(), f"Raw data directory does not exist: {raw_dir}")

    def test_processed_dir_exists(self):
        """Test that processed data directory exists."""
        processed_dir = get_processed_dir()
        self.assertTrue(processed_dir.exists(), f"Processed data directory does not exist: {processed_dir}")

    def test_artifacts_dir_exists(self):
        """Test that artifacts directory exists."""
        artifacts_dir = get_artifacts_dir()
        self.assertTrue(artifacts_dir.exists(), f"Artifacts directory does not exist: {artifacts_dir}")

    def test_tests_dir_exists(self):
        """Test that tests directory exists."""
        root = get_project_root()
        tests_dir = root / "code" / "tests"
        self.assertTrue(tests_dir.exists(), f"Tests directory does not exist: {tests_dir}")

    def test_state_dir_exists(self):
        """Test that state directory exists."""
        root = get_project_root()
        state_dir = root / "state"
        self.assertTrue(state_dir.exists(), f"State directory does not exist: {state_dir}")

def run_tests():
    """Run the tests and return results."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProjectStructure)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
