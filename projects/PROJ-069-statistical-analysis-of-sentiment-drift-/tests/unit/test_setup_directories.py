import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_directories import initialize_structure

class TestInitializeStructure:
    """Unit tests for directory initialization logic."""

    def test_creates_all_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/metadata",
            "results",
            "tests",
            "artifacts",
            "docs"
        ]
        
        created = initialize_structure(tmp_path)
        
        # Check count
        assert len(created) == len(required_dirs)
        
        # Check each directory exists
        for dir_name in required_dirs:
            expected_path = tmp_path / dir_name
            assert expected_path.exists(), f"Directory {expected_path} was not created"
            assert expected_path.is_dir(), f"{expected_path} is not a directory"

    def test_returns_absolute_paths(self, tmp_path):
        """Test that returned paths are absolute."""
        created = initialize_structure(tmp_path)
        
        for path_str in created:
            path = Path(path_str)
            assert path.is_absolute(), f"Path {path_str} is not absolute"

    def test_handles_existing_directories(self, tmp_path):
        """Test that existing directories are not recreated but still listed."""
        # Create one directory beforehand
        (tmp_path / "code").mkdir()
        
        created = initialize_structure(tmp_path)
        
        # Should still return all paths
        assert len(created) == 8
        assert any("code" in p for p in created)

    def test_nested_directory_creation(self, tmp_path):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        created = initialize_structure(tmp_path)
        
        raw_path = tmp_path / "data" / "raw"
        assert raw_path.exists()
        assert raw_path.is_dir()

    def test_raises_on_file_collision(self, tmp_path):
        """Test that an error is raised if a path exists but is a file."""
        # Create a file where a directory should be
        file_path = tmp_path / "code"
        file_path.touch()
        
        with pytest.raises(FileExistsError):
            initialize_structure(tmp_path)