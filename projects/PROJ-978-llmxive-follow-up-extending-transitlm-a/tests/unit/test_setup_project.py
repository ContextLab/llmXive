"""
Unit tests for the project setup script.

These tests verify that the required directory structure is created correctly.
"""
import os
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

# Add the project root to the path so we can import setup_project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project import main


class TestProjectSetup(unittest.TestCase):
    """Test cases for project setup functionality."""

    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up the temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_main_creates_all_directories(self):
        """Test that main() creates all required directories."""
        # Run the setup
        result = main()
        
        # Check return code
        self.assertEqual(result, 0, "main() should return 0 on success")
        
        # Verify each required directory exists
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/analysis",
            "models",
            "analysis",
            "tests",
            "docs"
        ]
        
        for dir_name in required_dirs:
            dir_path = Path(self.test_dir) / dir_name
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Directory {dir_name} should exist after setup"
            )

    def test_nested_directories_created(self):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        result = main()
        self.assertEqual(result, 0)
        
        # Test specific nested paths
        nested_paths = [
            "data/raw",
            "data/processed",
            "data/analysis"
        ]
        
        for path in nested_paths:
            full_path = Path(self.test_dir) / path
            self.assertTrue(
                full_path.exists() and full_path.is_dir(),
                f"Nested directory {path} should exist"
            )


if __name__ == "__main__":
    unittest.main()