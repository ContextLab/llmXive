"""
Integration Test for T001: Project Structure Verification.

This test verifies that the required directory structure and __init__.py
files have been created correctly.
"""
import unittest
import os
import sys
from pathlib import Path

class TestT001ProjectStructure(unittest.TestCase):
    """Test suite for verifying the project directory structure."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_dir = Path(__file__).parent.parent.parent
        self.required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "results",
            "specs",
            "tests",
            "tests/unit",
            "tests/integration",
            "code/pipeline",
            "code/schemas",
            "code/utils",
            "code/results",
            "code/scripts",
            "docs",
            "state",
            "logs"
        ]
        self.top_level_dirs = ["code", "tests", "data", "results", "specs"]

    def test_required_directories_exist(self):
        """Verify all required directories exist."""
        missing_dirs = []
        for dir_path in self.required_dirs:
            full_path = self.base_dir / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        self.assertEqual(
            len(missing_dirs), 0,
            f"Missing directories: {missing_dirs}"
        )

    def test_init_files_exist_in_code_subdirs(self):
        """Verify __init__.py files exist in code subdirectories."""
        missing_inits = []
        for dir_path in self.required_dirs:
            if dir_path.startswith("code"):
                full_path = self.base_dir / dir_path
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    missing_inits.append(dir_path)
        
        self.assertEqual(
            len(missing_inits), 0,
            f"Missing __init__.py in code dirs: {missing_inits}"
        )

    def test_init_files_exist_in_tests_subdirs(self):
        """Verify __init__.py files exist in tests subdirectories."""
        missing_inits = []
        for dir_path in self.required_dirs:
            if dir_path.startswith("tests"):
                full_path = self.base_dir / dir_path
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    missing_inits.append(dir_path)
        
        self.assertEqual(
            len(missing_inits), 0,
            f"Missing __init__.py in tests dirs: {missing_inits}"
        )

    def test_init_files_exist_in_top_level_dirs(self):
        """Verify __init__.py files exist in top-level directories."""
        missing_inits = []
        for dir_name in self.top_level_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    missing_inits.append(dir_name)
        
        self.assertEqual(
            len(missing_inits), 0,
            f"Missing __init__.py in top-level dirs: {missing_inits}"
        )

    def test_data_raw_directory_exists(self):
        """Specific test for data/raw directory."""
        data_raw = self.base_dir / "data" / "raw"
        self.assertTrue(
            data_raw.exists() and data_raw.is_dir(),
            "data/raw directory does not exist"
        )

    def test_data_processed_directory_exists(self):
        """Specific test for data/processed directory."""
        data_processed = self.base_dir / "data" / "processed"
        self.assertTrue(
            data_processed.exists() and data_processed.is_dir(),
            "data/processed directory does not exist"
        )

    def test_results_directory_exists(self):
        """Specific test for results directory."""
        results = self.base_dir / "results"
        self.assertTrue(
            results.exists() and results.is_dir(),
            "results directory does not exist"
        )

    def test_specs_directory_exists(self):
        """Specific test for specs directory."""
        specs = self.base_dir / "specs"
        self.assertTrue(
            specs.exists() and specs.is_dir(),
            "specs directory does not exist"
        )

    def test_tests_unit_directory_exists(self):
        """Specific test for tests/unit directory."""
        tests_unit = self.base_dir / "tests" / "unit"
        self.assertTrue(
            tests_unit.exists() and tests_unit.is_dir(),
            "tests/unit directory does not exist"
        )

    def test_tests_integration_directory_exists(self):
        """Specific test for tests/integration directory."""
        tests_integration = self.base_dir / "tests" / "integration"
        self.assertTrue(
            tests_integration.exists() and tests_integration.is_dir(),
            "tests/integration directory does not exist"
        )

if __name__ == "__main__":
    unittest.main()