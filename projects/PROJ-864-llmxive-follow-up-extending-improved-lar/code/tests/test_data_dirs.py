import os
import sys
import unittest
from pathlib import Path

# Add the code directory to the path so we can import from it
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.setup_data_dirs import setup_data_directories
from utils.logging import setup_logging

class TestDataDirectories(unittest.TestCase):
    """Test cases for data directory setup functionality."""

    def setUp(self):
        """Set up test fixtures."""
        setup_logging()
        self.test_data_base = code_dir / "data"
        self.expected_dirs = {
            "raw": self.test_data_base / "raw",
            "processed": self.test_data_base / "processed",
            "artifacts": self.test_data_base / "artifacts",
        }

    def tearDown(self):
        """Clean up after tests."""
        # Note: We don't delete the directories as they may be needed by other tests
        # In a real scenario, we might clean up test-specific temporary directories
        pass

    def test_setup_data_directories_creates_all_dirs(self):
        """Test that setup_data_directories creates all required directories."""
        result_dirs = setup_data_directories()
        
        # Check that all expected directories exist
        for name, expected_path in self.expected_dirs.items():
            self.assertTrue(
                expected_path.exists(),
                f"Directory {expected_path} was not created"
            )
            self.assertTrue(
                expected_path.is_dir(),
                f"Path {expected_path} is not a directory"
            )

    def test_setup_data_directories_returns_correct_paths(self):
        """Test that the function returns the correct directory paths."""
        result_dirs = setup_data_directories()
        
        # Check that the returned paths match expected
        for expected_path in self.expected_dirs.values():
            self.assertIn(
                expected_path,
                result_dirs,
                f"Expected path {expected_path} not in returned list"
            )

    def test_setup_data_directories_idempotent(self):
        """Test that calling setup_data_directories multiple times doesn't fail."""
        # First call
        dirs1 = setup_data_directories()
        
        # Second call
        dirs2 = setup_data_directories()
        
        # Both should succeed and return the same directories
        self.assertEqual(len(dirs1), len(dirs2))
        for d1, d2 in zip(sorted(dirs1), sorted(dirs2)):
            self.assertEqual(d1, d2)

    def test_data_base_directory_exists(self):
        """Test that the base data directory exists after setup."""
        setup_data_directories()
        self.assertTrue(
            self.test_data_base.exists(),
            "Base data directory does not exist"
        )
        self.assertTrue(
            self.test_data_base.is_dir(),
            "Base data path is not a directory"
        )

def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDataDirectories)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result

if __name__ == "__main__":
    run_tests()