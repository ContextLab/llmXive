import pytest
import os
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_dirs import create_directories

class TestSetupDirs:
    """
    Tests for the directory creation logic in setup_dirs.py.
    """

    def test_create_directories_returns_true(self):
        """Test that create_directories returns True on success."""
        # We expect this to succeed in a standard environment
        result = create_directories()
        assert result is True

    def test_directories_exist_after_creation(self):
        """Test that required directories exist after running create_directories."""
        # Run creation first
        create_directories()
        
        project_root = Path(__file__).resolve().parent.parent
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "outputs",
            "tests",
            "projects/PROJ-540-the-influence-of-social-media-doomscroll"
        ]

        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} is not a directory."

    def test_gitkeep_files_exist(self):
        """Test that .gitkeep files exist in all required directories."""
        # Run creation first
        create_directories()
        
        project_root = Path(__file__).resolve().parent.parent
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "outputs",
            "tests",
            "projects/PROJ-540-the-influence-of-social-media-doomscroll"
        ]

        for dir_path in required_dirs:
            full_path = project_root / dir_path
            gitkeep_path = full_path / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep file missing in {full_path}"