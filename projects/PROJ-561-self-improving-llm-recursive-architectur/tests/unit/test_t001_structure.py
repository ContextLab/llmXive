"""
Unit test for T001: Project Structure Creation and Verification.
Verifies that the required directories and __init__.py files exist.
"""
import unittest
import os
import sys
from pathlib import Path

# Add code/ to path to import setup scripts if needed, though we mostly check filesystem
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

class TestProjectStructure(unittest.TestCase):
    """Tests for T001 project structure creation."""

    def setUp(self):
        """Define required paths relative to project root."""
        # Assuming tests are run from project root or code/tests/
        # We need to find the project root.
        # If running from code/tests/unit/, project root is ../../
        # If running from root, it's .
        # We'll try to detect or assume root is the parent of 'code'
        current_file = Path(__file__).resolve()
        # Try to find 'code' directory upwards
        root = current_file
        while root.parent != root:
            if (root / 'code').exists():
                break
            root = root.parent
        self.project_root = root

    def test_required_directories_exist(self):
        """Verify all required directories exist."""
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration"
        ]

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Required directory missing: {dir_path}"
            )

    def test_init_files_exist(self):
        """Verify __init__.py files exist in all required directories."""
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration"
        ]

        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            init_file = dir_path / "__init__.py"
            self.assertTrue(
                init_file.exists(),
                f"__init__.py missing in {dir_path}"
            )
            # Optional: Check if file is not empty (as per "initialize" requirement)
            # self.assertGreater(
            #     init_file.stat().st_size,
            #     0,
            #     f"__init__.py is empty in {dir_path}"
            # )

    def test_setup_verify_script_exists(self):
        """Verify the verification script exists."""
        script_path = self.project_root / "code" / "setup_verify.py"
        self.assertTrue(script_path.exists(), "setup_verify.py missing")

    def test_setup_project_script_exists(self):
        """Verify the creation script exists."""
        script_path = self.project_root / "code" / "setup_project.py"
        self.assertTrue(script_path.exists(), "setup_project.py missing")

if __name__ == '__main__':
    unittest.main()