"""
Unit tests for project structure creation and verification.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the module
# This assumes the test is run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project_structure import create_structure

class TestProjectStructure:
    """Tests for the create_structure function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/utils",
            "tests",
            "tests/contract",
            "tests/unit",
            "tests/integration",
            "docs",
            "state",
        ]

        created = create_structure(tmp_path)

        for dir_name in required_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"{dir_name} is not a directory"

    def test_creates_additional_directories(self, tmp_path):
        """Verify that additional utility directories are created."""
        additional_dirs = [
            "data/models",
            "figures",
            "logs",
        ]

        create_structure(tmp_path)

        for dir_name in additional_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"

    def test_handles_existing_directories(self, tmp_path):
        """Verify that the function handles existing directories gracefully."""
        # Create one directory manually
        existing_dir = tmp_path / "data" / "raw"
        existing_dir.mkdir(parents=True)

        # Run the function
        created = create_structure(tmp_path)

        # Should not raise an error
        assert existing_dir.exists()
        # The directory should not be in the 'created' list if it already existed
        # (depending on implementation, but logically it shouldn't be 'newly' created)
        # The current implementation only adds to 'created' if mkdir was called
        assert str(existing_dir) not in created

    def test_returns_list_of_created_paths(self, tmp_path):
        """Verify that the function returns a list of created paths."""
        result = create_structure(tmp_path)

        assert isinstance(result, list)
        assert len(result) > 0
        for path_str in result:
            assert Path(path_str).exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])