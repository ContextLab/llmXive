import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_structure

class TestSetupProjectStructure:
    """Unit tests for the project structure creation logic."""

    def test_create_structure_creates_all_directories(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
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
                "state"
            ]
            
            result = create_structure(base_path)
            
            # Check that all directories were reported as created
            assert len(result) == len(required_dirs)
            
            # Check that each directory actually exists on disk
            for dir_name in required_dirs:
                full_path = base_path / dir_name
                assert full_path.exists(), f"Directory {dir_name} was not created"
                assert full_path.is_dir(), f"Path {dir_name} is not a directory"

    def test_create_structure_handles_existing_directories(self):
        """Test that the function doesn't fail if directories already exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # Pre-create one of the directories
            (base_path / "code").mkdir()
            
            # Should not raise an exception
            result = create_structure(base_path)
            
            # Should still report all directories
            assert "code" in result

    def test_create_structure_returns_absolute_paths(self):
        """Test that returned paths are absolute."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir).resolve()
            result = create_structure(base_path)
            
            for path_str in result.values():
                assert Path(path_str).is_absolute(), f"Path {path_str} is not absolute"

    def test_create_structure_nested_directories(self):
        """Test that nested directories (e.g., data/raw) are created correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            result = create_structure(base_path)
            
            # Check nested directory specifically
            assert "data/raw" in result
            raw_path = Path(result["data/raw"])
            assert raw_path.exists()
            assert raw_path.is_dir()
            # Check parent was also created
            assert raw_path.parent.exists()
            assert raw_path.parent.is_dir()