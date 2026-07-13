"""
T001a Tests: Verify project directory structure creation.

Tests ensure that the setup script creates the required directories
and that they exist after execution.
"""
import os
import tempfile
import pytest
import shutil
import sys

# Add the parent directory to the path so we can import the setup script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from code.setup_directories import create_directory_structure

class TestDirectoryStructure:
    """Test cases for directory structure creation."""

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to simulate project root."""
        temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
        yield temp_dir
        # Cleanup after test
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    def test_creates_code_directory(self, temp_project_root):
        """Verify 'code' directory is created."""
        create_directory_structure(temp_project_root)
        assert os.path.isdir(os.path.join(temp_project_root, "code"))

    def test_creates_data_subdirectories(self, temp_project_root):
        """Verify all data subdirectories are created."""
        create_directory_structure(temp_project_root)
        data_subdirs = ["raw", "processed", "results", "interim"]
        for subdir in data_subdirs:
            path = os.path.join(temp_project_root, "data", subdir)
            assert os.path.isdir(path), f"Missing: data/{subdir}"

    def test_creates_tests_directory(self, temp_project_root):
        """Verify 'tests' directory is created."""
        create_directory_structure(temp_project_root)
        assert os.path.isdir(os.path.join(temp_project_root, "tests"))

    def test_creates_docs_directory(self, temp_project_root):
        """Verify 'docs' directory is created."""
        create_directory_structure(temp_project_root)
        assert os.path.isdir(os.path.join(temp_project_root, "docs"))

    def test_idempotent_creation(self, temp_project_root):
        """Verify running the script twice doesn't cause errors."""
        create_directory_structure(temp_project_root)
        # Run again
        create_directory_structure(temp_project_root)
        # Should still exist
        assert os.path.isdir(os.path.join(temp_project_root, "code"))
        assert os.path.isdir(os.path.join(temp_project_root, "data", "raw"))