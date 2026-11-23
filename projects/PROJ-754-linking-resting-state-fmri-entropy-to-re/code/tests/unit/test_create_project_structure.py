import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the functions to test
# We need to add the code directory to sys.path to import scripts.create_project_structure
# assuming the test runner sets up the path correctly or we do it here.
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.create_project_structure import get_project_root, ensure_directory

class TestDirectoryCreation:
    def test_ensure_directory_creates_new(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        new_dir = tmp_path / "new_folder"
        assert not new_dir.exists()
        
        result = ensure_directory(new_dir)
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_existing(self, tmp_path):
        """Test that ensure_directory returns True for existing directory."""
        existing_dir = tmp_path / "existing_folder"
        existing_dir.mkdir()
        assert existing_dir.exists()
        
        result = ensure_directory(existing_dir)
        
        assert result is True
        assert existing_dir.exists()

    def test_get_project_root_fallback(self, tmp_path):
        """Test get_project_root fallback to current directory if no marker found."""
        # Temporarily change directory to a temp folder with no markers
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Ensure no .git or pyproject.toml
            root = get_project_root()
            # Should fallback to cwd (tmp_path)
            assert root == Path(tmp_path)
        finally:
            os.chdir(old_cwd)

    def test_directory_creation_logic(self, tmp_path):
        """Test the logic of creating multiple directories."""
        # Simulate the logic in main()
        dirs_to_create = ["src", "data", "tests/unit"]
        created = []
        
        for d in dirs_to_create:
            path = tmp_path / d
            if ensure_directory(path):
                created.append(d)
        
        assert len(created) == 3
        assert (tmp_path / "src").exists()
        assert (tmp_path / "data").exists()
        assert (tmp_path / "tests/unit").exists()