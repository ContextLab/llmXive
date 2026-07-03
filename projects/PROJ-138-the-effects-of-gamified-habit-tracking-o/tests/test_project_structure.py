"""
Tests for the project structure setup.
Verifies that all required directories and .gitkeep files exist.
"""
import os
import unittest
import sys

# Add the root to the path if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestProjectStructure(unittest.TestCase):
    """Test suite for verifying project directory structure."""

    REQUIRED_DIRS = [
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/consent"
    ]

    def test_all_directories_exist(self):
        """Assert all required directories exist."""
        missing_dirs = []
        for dir_path in self.REQUIRED_DIRS:
            if not os.path.isdir(dir_path):
                missing_dirs.append(dir_path)

        self.assertEqual(len(missing_dirs), 0, f"Missing directories: {missing_dirs}")

    def test_gitkeep_files_exist(self):
        """Assert .gitkeep files exist in all required directories."""
        missing_gitkeeps = []
        for dir_path in self.REQUIRED_DIRS:
            gitkeep_path = os.path.join(dir_path, ".gitkeep")
            if not os.path.isfile(gitkeep_path):
                missing_gitkeeps.append(gitkeep_path)

        self.assertEqual(len(missing_gitkeeps), 0, f"Missing .gitkeep files: {missing_gitkeeps}")

    def test_gitkeep_files_are_not_empty(self):
        """Assert .gitkeep files have content (to ensure they are tracked)."""
        empty_gitkeeps = []
        for dir_path in self.REQUIRED_DIRS:
            gitkeep_path = os.path.join(dir_path, ".gitkeep")
            if os.path.isfile(gitkeep_path):
                with open(gitkeep_path, "r") as f:
                    content = f.read().strip()
                    if not content:
                        empty_gitkeeps.append(gitkeep_path)

        # We expect them to have at least a comment
        self.assertEqual(len(empty_gitkeeps), 0, f"Empty .gitkeep files: {empty_gitkeeps}")


if __name__ == "__main__":
    unittest.main()