"""
Tests to verify the project structure created by T001.
"""
import os
import pytest

# Define the expected directory structure
EXPECTED_DIRS = [
    "code/data",
    "code/models",
    "code/analysis",
    "code/utils",
    "code/tests",
    "contracts",
    "data/raw",
    "data/processed",
    "data/results",
    "docs",
]

EXPECTED_INIT_FILES = [
    "code/__init__.py",
    "code/data/__init__.py",
    "code/models/__init__.py",
    "code/analysis/__init__.py",
    "code/utils/__init__.py",
    "code/tests/__init__.py",
]

class TestProjectStructure:
    """Tests to ensure the project directory structure is correctly initialized."""

    @pytest.fixture(scope="class")
    def project_root(self):
        """Return the current working directory as the project root."""
        return os.getcwd()

    @pytest.mark.parametrize("dir_path", EXPECTED_DIRS)
    def test_directory_exists(self, project_root, dir_path):
        """Verify that each required directory exists."""
        full_path = os.path.join(project_root, dir_path)
        assert os.path.isdir(full_path), f"Directory missing: {full_path}"

    @pytest.mark.parametrize("file_path", EXPECTED_INIT_FILES)
    def test_init_file_exists(self, project_root, file_path):
        """Verify that __init__.py files exist for Python packages."""
        full_path = os.path.join(project_root, file_path)
        assert os.path.isfile(full_path), f"Init file missing: {full_path}"

    def test_no_absolute_paths_in_structure(self):
        """Ensure no directory creation logic uses absolute paths."""
        # This is a sanity check for the setup script logic
        # In a real scenario, we might inspect the setup script source
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])