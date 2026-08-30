import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ensure code directory is in path if running from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setup_directories import create_code_directories
from utils.logging import get_logger


class TestSetupDirectories(unittest.TestCase):
    def setUp(self):
        """Create a temporary directory to simulate the project root."""
        self.test_dir = tempfile.mkdtemp()
        self.project_root = Path(self.test_dir)
        self.logger = get_logger(__name__)

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_directories(self):
        """Test that create_code_directories creates the required directories."""
        result = create_code_directories(self.project_root, self.logger)

        self.assertTrue(result, "Function should return True on success")

        expected_dirs = [
            self.project_root / "code" / "data",
            self.project_root / "code" / "tests",
            self.project_root / "code" / "utils",
        ]

        for dir_path in expected_dirs:
            self.assertTrue(
                dir_path.is_dir(),
                f"Directory {dir_path} should exist after creation"
            )

    def test_create_directories_idempotent(self):
        """Test that running the function twice does not raise errors."""
        # First run
        create_code_directories(self.project_root, self.logger)
        # Second run (should succeed with exist_ok=True)
        result = create_code_directories(self.project_root, self.logger)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()