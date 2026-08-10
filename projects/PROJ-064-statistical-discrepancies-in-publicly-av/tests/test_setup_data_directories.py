"""
Tests for T004: Setup data directory structure.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We need to adjust the import path if running tests differently,
# but assuming standard pytest discovery from project root:
import sys
from pathlib import Path

# Ensure code/ is in path for imports
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_data_directories import setup_data_directories


class TestSetupDataDirectories:
    def test_creates_required_directories(self, tmp_path):
        """Test that the function creates data/raw, data/processed, and state."""
        # Arrange
        expected_dirs = ["data/raw", "data/processed", "state"]

        # Act
        setup_data_directories(tmp_path)

        # Assert
        for dir_name in expected_dirs:
            full_path = tmp_path / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"Path {dir_name} is not a directory"

    def test_idempotent(self, tmp_path):
        """Test that running the function twice does not raise an error."""
        # Act & Assert: Should not raise
        setup_data_directories(tmp_path)
        setup_data_directories(tmp_path)

        # Verify directories still exist
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "data/processed").exists()
        assert (tmp_path / "state").exists()

    def test_creates_gitkeep_files(self, tmp_path):
        """Test that .gitkeep files are created in the directories."""
        setup_data_directories(tmp_path)

        expected_gitkeeps = [
            tmp_path / "data/raw" / ".gitkeep",
            tmp_path / "data/processed" / ".gitkeep",
            tmp_path / "state" / ".gitkeep",
        ]

        for gitkeep in expected_gitkeeps:
            assert gitkeep.exists(), f"{gitkeep} was not created"
            # Verify content is not empty (optional but good practice)
            content = gitkeep.read_text()
            assert len(content) > 0, f"{gitkeep} is empty"