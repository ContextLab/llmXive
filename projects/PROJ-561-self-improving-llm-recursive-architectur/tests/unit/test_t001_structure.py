"""
Unit tests for T001: Project Structure Creation.

These tests verify that the required directory structure and
__init__.py files exist as specified in the task.
"""
import os
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

class TestT001ProjectStructure(unittest.TestCase):
    """Test cases for project structure verification."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.root = project_root
        cls.required_dirs = [
            "code",
            "code/utils",
            "code/pipeline",
            "code/results",
            "code/schemas",
            "data",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration",
        ]
        cls.required_init_files = [
            "code/__init__.py",
            "code/utils/__init__.py",
            "code/pipeline/__init__.py",
            "code/results/__init__.py",
            "code/schemas/__init__.py",
            "data/__init__.py",
            "data/raw/__init__.py",
            "data/processed/__init__.py",
            "results/__init__.py",
            "specs/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
        ]

    def test_required_directories_exist(self):
        """Verify all required directories exist."""
        for dir_path in self.required_dirs:
            full_path = self.root / dir_path
            self.assertTrue(
                full_path.exists(),
                f"Required directory missing: {dir_path}"
            )
            self.assertTrue(
                full_path.is_dir(),
                f"Path exists but is not a directory: {dir_path}"
            )

    def test_required_init_files_exist(self):
        """Verify all required __init__.py files exist."""
        for init_path in self.required_init_files:
            full_path = self.root / init_path
            self.assertTrue(
                full_path.exists(),
                f"Required __init__.py missing: {init_path}"
            )
            self.assertTrue(
                full_path.is_file(),
                f"Path exists but is not a file: {init_path}"
            )

    def test_init_files_are_importable(self):
        """Verify that __init__.py files allow package imports."""
        # Test that we can import the main packages
        try:
            import code
            import code.utils
            import code.pipeline
            import code.results
            import code.schemas
            import data
            import data.raw
            import data.processed
            import results
            import specs
            import tests
            import tests.unit
            import tests.integration
        except ImportError as e:
            self.fail(f"Failed to import package due to missing __init__.py: {e}")

    def test_directory_structure_matches_spec(self):
        """Verify the directory structure matches the T001 specification exactly."""
        expected_structure = {
            "code": ["utils", "pipeline", "results", "schemas"],
            "data": ["raw", "processed"],
            "tests": ["unit", "integration"],
        }
        
        for parent, children in expected_structure.items():
            parent_path = self.root / parent
            self.assertTrue(
                parent_path.exists(),
                f"Parent directory missing: {parent}"
            )
            
            for child in children:
                child_path = parent_path / child
                self.assertTrue(
                    child_path.exists(),
                    f"Child directory missing: {parent}/{child}"
                )

if __name__ == "__main__":
    unittest.main()