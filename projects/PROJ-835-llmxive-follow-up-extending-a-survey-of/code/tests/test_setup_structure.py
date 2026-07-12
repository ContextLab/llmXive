import os
import tempfile
import shutil
import pytest
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from setup_structure import create_structure

class TestSetupStructure:
    """Tests for the project structure creation utility."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        required_dirs = [
            "src",
            "src/data",
            "src/models",
            "src/utils",
            "tests",
            "tests/contract",
            "tests/integration",
            "data",
            "models",
            "results",
            "state",
            "state/projects",
            "figures",
        ]
        
        create_structure(str(tmp_path))
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_does_not_fail_on_existing_directories(self, tmp_path):
        """Verify that the function handles existing directories gracefully."""
        # Create some directories first
        (tmp_path / "src").mkdir()
        (tmp_path / "data").mkdir()
        
        # Should not raise an exception
        create_structure(str(tmp_path))
        
        assert (tmp_path / "src").exists()
        assert (tmp_path / "data").exists()

    def test_raises_on_file_path_collision(self, tmp_path):
        """Verify that the function raises an error if a path exists as a file."""
        # Create a file where a directory should be
        file_path = tmp_path / "src"
        file_path.touch()
        
        with pytest.raises(RuntimeError, match="not a directory"):
            create_structure(str(tmp_path))

    def test_creates_nested_directories(self, tmp_path):
        """Verify that nested directories are created correctly."""
        create_structure(str(tmp_path))
        
        nested_dirs = [
            "src/data",
            "src/models",
            "src/utils",
            "tests/contract",
            "tests/integration",
            "state/projects",
        ]
        
        for dir_name in nested_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Nested directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_output_messages(self, tmp_path, capsys):
        """Verify that the function outputs status messages."""
        create_structure(str(tmp_path))
        captured = capsys.readouterr()
        
        assert "Project structure setup complete" in captured.out
        assert "directories created" in captured.out