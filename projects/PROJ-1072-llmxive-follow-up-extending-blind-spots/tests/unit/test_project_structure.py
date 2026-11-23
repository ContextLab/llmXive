"""
Unit tests for T001: Project Structure Creation.
Verifies that the required directory hierarchy exists.
"""
import os
import pytest
from pathlib import Path

# Define the expected directory structure
EXPECTED_DIRS = [
    "code",
    "code/utils",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/filtered",
    "data/traces",
    "data/results",
    "data/validation",
    "data/pilot",
    "specs",
    "specs/001-blind-spots-order-analysis",
    "specs/001-blind-spots-order-analysis/contracts",
    "state",
    "figures",
]

@pytest.fixture
def project_root():
    """Return the project root path (current working directory)."""
    return Path(".")

class TestProjectStructure:
    """Tests to verify the project directory structure exists."""

    @pytest.mark.parametrize("dir_name", EXPECTED_DIRS)
    def test_directory_exists(self, project_root, dir_name):
        """Verify that each required directory exists."""
        full_path = project_root / dir_name
        assert full_path.exists(), f"Directory does not exist: {full_path}"
        assert full_path.is_dir(), f"Path exists but is not a directory: {full_path}"

    def test_critical_paths_exist(self, project_root):
        """Verify critical paths required for pipeline execution."""
        critical_paths = ["code", "tests", "data/filtered", "data/traces"]
        
        for path_str in critical_paths:
            path = project_root / path_str
            assert path.exists(), f"Critical path missing: {path}"
            assert path.is_dir(), f"Critical path is not a directory: {path}"

    def test_code_directory_is_writable(self, project_root):
        """Verify that the code directory is writable."""
        code_dir = project_root / "code"
        assert os.access(code_dir, os.W_OK), f"Code directory is not writable: {code_dir}"

    def test_data_directory_is_writable(self, project_root):
        """Verify that the data directory is writable."""
        data_dir = project_root / "data"
        assert os.access(data_dir, os.W_OK), f"Data directory is not writable: {data_dir}"

    def test_tests_directory_is_writable(self, project_root):
        """Verify that the tests directory is writable."""
        tests_dir = project_root / "tests"
        assert os.access(tests_dir, os.W_OK), f"Tests directory is not writable: {tests_dir}"