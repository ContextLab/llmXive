"""
Unit tests to verify the directory structure created by T004a.
"""
import os
from pathlib import Path
import pytest

class TestDirectoryStructure:
    """Tests for the required directory structure."""

    REQUIRED_DIRS = [
        "data/raw",
        "data/processed",
        "artifacts/profiles",
        "artifacts/stability",
        "artifacts/meta_analysis",
        "artifacts/checkpoints"
    ]

    def test_all_required_directories_exist(self):
        """Verify all required directories exist."""
        for dir_path in self.REQUIRED_DIRS:
            path = Path(dir_path)
            assert path.exists(), f"Directory {dir_path} does not exist"
            assert path.is_dir(), f"{dir_path} is not a directory"

    def test_gitkeep_files_exist(self):
        """Verify .gitkeep files exist in all required directories."""
        for dir_path in self.REQUIRED_DIRS:
            path = Path(dir_path)
            gitkeep_path = path / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep file missing in {dir_path}"

    def test_directory_structure_is_valid(self):
        """Verify the directory structure matches the expected pattern."""
        # Check data directories
        assert Path("data/raw").exists()
        assert Path("data/processed").exists()
        
        # Check artifacts directories
        assert Path("artifacts/profiles").exists()
        assert Path("artifacts/stability").exists()
        assert Path("artifacts/meta_analysis").exists()
        assert Path("artifacts/checkpoints").exists()

    def test_no_extra_files_in_empty_directories(self):
        """Verify that the newly created directories only contain .gitkeep files."""
        for dir_path in self.REQUIRED_DIRS:
            path = Path(dir_path)
            files = list(path.iterdir())
            # Should only contain .gitkeep
            non_gitkeep_files = [f for f in files if f.name != ".gitkeep"]
            assert len(non_gitkeep_files) == 0, \
                f"Directory {dir_path} contains unexpected files: {non_gitkeep_files}"
