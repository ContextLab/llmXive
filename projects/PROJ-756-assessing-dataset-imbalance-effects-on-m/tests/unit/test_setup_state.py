"""
Unit tests for T001g: Verify state directory creation logic.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# We need to import from the sibling module in code/
import sys
from code.setup_state import create_state_directory

class TestStateDirectoryCreation:
    """Tests for the create_state_directory function."""

    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that the function creates the 'state' directory if it doesn't exist."""
        state_dir_path = tmp_path / "state"
        assert not state_dir_path.exists()

        result = create_state_directory(tmp_path)

        assert result == state_dir_path
        assert result.exists()
        assert result.is_dir()

    def test_returns_existing_directory(self, tmp_path):
        """Test that the function returns the path if the directory already exists."""
        state_dir_path = tmp_path / "state"
        state_dir_path.mkdir(parents=True, exist_ok=True)
        assert state_dir_path.exists()

        result = create_state_directory(tmp_path)

        assert result == state_dir_path
        assert result.is_dir()

    def test_creates_parent_directories(self, tmp_path):
        """Test that the function creates parent directories if necessary (though 'state' is direct child)."""
        # This test ensures the logic handles nested paths correctly if the implementation changes
        # or if we test a nested structure.
        # For T001g, 'state' is a direct child, but the function uses parents=True.
        nested_project = tmp_path / "sub" / "project"
        nested_project.mkdir(parents=True, exist_ok=True)
        
        state_dir_path = nested_project / "state"
        assert not state_dir_path.exists()

        result = create_state_directory(nested_project)

        assert result == state_dir_path
        assert result.exists()
        assert result.is_dir()

    def test_no_side_effects_on_other_dirs(self, tmp_path):
        """Test that the function does not create unexpected directories."""
        # Create some other directories
        (tmp_path / "data").mkdir()
        (tmp_path / "code").mkdir()

        create_state_directory(tmp_path)

        # Check that only 'state' was created (plus existing ones)
        contents = set([p.name for p in tmp_path.iterdir()])
        assert "state" in contents
        assert "data" in contents
        assert "code" in contents
        assert len(contents) == 3  # Ensure no extra directories were created