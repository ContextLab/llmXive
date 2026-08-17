"""
Test script to verify the directory structure created by T002.
Ensures 'code', 'artifacts', and 'tests' directories exist at the project root.
"""
import os
import pytest
import sys

# Add project root to path if running from tests/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

REQUIRED_DIRS = [
    "code",
    "artifacts",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/assets"
]

class TestDirectoryStructure:
    """Test cases for verifying project directory structure."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure we are testing relative to the project root."""
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        yield

    @pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
    def test_directory_exists(self, dir_name):
        """Verify that each required directory exists."""
        full_path = os.path.join(self.base_path, dir_name)
        assert os.path.exists(full_path), f"Directory missing: {full_path}"
        assert os.path.isdir(full_path), f"Path is not a directory: {full_path}"

    def test_code_directory_has_subdirs(self):
        """Verify that code/ directory is present (T002 requirement)."""
        code_path = os.path.join(self.base_path, "code")
        assert os.path.isdir(code_path), "code/ directory missing"

    def test_artifacts_directory_has_subdirs(self):
        """Verify that artifacts/ directory is present (T002 requirement)."""
        artifacts_path = os.path.join(self.base_path, "artifacts")
        assert os.path.isdir(artifacts_path), "artifacts/ directory missing"

    def test_tests_directory_has_subdirs(self):
        """Verify that tests/ directory is present (T002 requirement)."""
        tests_path = os.path.join(self.base_path, "tests")
        assert os.path.isdir(tests_path), "tests/ directory missing"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
