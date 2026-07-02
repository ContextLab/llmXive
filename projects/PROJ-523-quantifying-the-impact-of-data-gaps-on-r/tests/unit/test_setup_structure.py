"""
Unit tests to verify the project directory structure was created correctly.
"""
import os
import pytest
import subprocess
import sys

REQUIRED_DIRS = [
    "code/simulation",
    "code/gap_filling",
    "code/analysis",
    "code/pipeline",
    "data/raw",
    "data/derived",
    "data/metadata",
    "data/results",
    "tests/contract",
    "tests/unit",
    "tests/integration"
]

@pytest.fixture(scope="module", autouse=True)
def ensure_structure():
    """Ensure the project structure exists before running tests."""
    # Run the setup script if any directory is missing
    missing = [d for d in REQUIRED_DIRS if not os.path.exists(d)]
    if missing:
        subprocess.run([sys.executable, "code/setup_project_structure.py"], check=True)

class TestProjectStructure:
    """Tests for verifying the project directory structure."""

    @pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
    def test_directory_exists(self, dir_path):
        """Verify that each required directory exists."""
        assert os.path.exists(dir_path), f"Directory missing: {dir_path}"
        assert os.path.isdir(dir_path), f"Not a directory: {dir_path}"

    def test_all_required_directories_present(self):
        """Verify all required directories are present."""
        for dir_path in REQUIRED_DIRS:
            assert os.path.exists(dir_path), f"Missing required directory: {dir_path}"
            assert os.path.isdir(dir_path), f"Required path is not a directory: {dir_path}"

    def test_code_structure_isolation(self):
        """Verify code directories are properly separated."""
        code_dirs = [d for d in REQUIRED_DIRS if d.startswith("code/")]
        assert len(code_dirs) == 4, f"Expected 4 code subdirectories, found {len(code_dirs)}"
        
        expected_code = {"code/simulation", "code/gap_filling", "code/analysis", "code/pipeline"}
        actual_code = set(code_dirs)
        assert expected_code == actual_code, f"Code directories mismatch: {expected_code} != {actual_code}"

    def test_data_structure_isolation(self):
        """Verify data directories are properly separated."""
        data_dirs = [d for d in REQUIRED_DIRS if d.startswith("data/")]
        assert len(data_dirs) == 4, f"Expected 4 data subdirectories, found {len(data_dirs)}"
        
        expected_data = {"data/raw", "data/derived", "data/metadata", "data/results"}
        actual_data = set(data_dirs)
        assert expected_data == actual_data, f"Data directories mismatch: {expected_data} != {actual_data}"

    def test_test_structure_isolation(self):
        """Verify test directories are properly separated."""
        test_dirs = [d for d in REQUIRED_DIRS if d.startswith("tests/")]
        assert len(test_dirs) == 3, f"Expected 3 test subdirectories, found {len(test_dirs)}"
        
        expected_tests = {"tests/contract", "tests/unit", "tests/integration"}
        actual_tests = set(test_dirs)
        assert expected_tests == actual_tests, f"Test directories mismatch: {expected_tests} != {actual_tests}"
