"""
Unit tests for the scaffold utility.
"""
import os
import tempfile
from pathlib import Path
import shutil

import pytest

# Import the module under test
# Adjust import path based on project structure
try:
    from code.utils.scaffold import verify_project_root, create_directories, main
except ImportError:
    # Fallback for when tests are run from a different context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from utils.scaffold import verify_project_root, create_directories, main


class TestVerifyProjectRoot:
    """Tests for verify_project_root function."""

    def test_existing_directory(self, tmp_path):
        """Test that an existing directory is recognized as valid."""
        assert verify_project_root(tmp_path) is True

    def test_non_existent_path(self, tmp_path):
        """Test that a non-existent path is rejected."""
        non_existent = tmp_path / "does_not_exist"
        assert verify_project_root(non_existent) is False

    def test_file_instead_of_directory(self, tmp_path):
        """Test that a file is rejected as a project root."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        assert verify_project_root(file_path) is False


class TestCreateDirectories:
    """Tests for create_directories function."""

    def test_creates_single_directory(self, tmp_path):
        """Test creation of a single directory."""
        create_directories(tmp_path, ["new_dir"])
        assert (tmp_path / "new_dir").exists()
        assert (tmp_path / "new_dir").is_dir()

    def test_creates_nested_directories(self, tmp_path):
        """Test creation of nested directories."""
        create_directories(tmp_path, ["parent/child/grandchild"])
        assert (tmp_path / "parent" / "child" / "grandchild").exists()

    def test_existent_ok(self, tmp_path):
        """Test that existing directories are not affected (exist_ok=True)."""
        # Create a directory first
        (tmp_path / "existing").mkdir()
        # Try to create it again
        create_directories(tmp_path, ["existing"])
        assert (tmp_path / "existing").exists()

    def test_creates_multiple_directories(self, tmp_path):
        """Test creation of multiple directories."""
        dirs = ["dir1", "dir2", "dir3"]
        create_directories(tmp_path, dirs)
        for d in dirs:
            assert (tmp_path / d).exists()


class TestScaffoldIntegration:
    """Integration tests for the scaffold script."""

    def test_full_scaffold_run(self, tmp_path):
        """Test the full scaffold run creates expected directories."""
        # Change to tmp_path to simulate running from project root
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Define the expected directories (matching the main script)
            expected_dirs = [
                "code",
                "data",
                "contracts",
                os.path.join("data", "results"),
                "docs",
                "state",
                "tests",
                "src",
            ]
            
            # Run the main function (which will use tmp_path as root due to cwd change)
            # Note: In a real scenario, the script would detect the root differently.
            # Here we test the directory creation logic directly.
            create_directories(tmp_path, expected_dirs)
            
            # Verify all directories were created
            for dir_name in expected_dirs:
                full_path = tmp_path / dir_name
                assert full_path.exists(), f"Directory {dir_name} was not created"
                assert full_path.is_dir(), f"{dir_name} is not a directory"
        finally:
            os.chdir(original_cwd)