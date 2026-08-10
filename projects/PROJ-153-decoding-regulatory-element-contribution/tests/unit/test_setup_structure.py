import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project_structure import create_directories

class TestProjectStructure:
    """Tests for project directory creation logic."""

    def test_directories_exist_after_creation(self, tmp_path, monkeypatch):
        """Verify that create_directories creates the expected folders."""
        # Change to temp directory for testing
        monkeypatch.chdir(tmp_path)
        
        # Mock the base directory to be the temp path
        original_cwd = Path.cwd()
        
        # Run the function
        create_directories()
        
        # Verify expected directories exist
        expected_dirs = [
            "code", "tests", "data", "results",
            "data/raw", "data/processed",
            "results/figures", "results/tables",
            "specs"
        ]
        
        for dir_name in expected_dirs:
            target = original_cwd / dir_name
            assert target.exists(), f"Directory {dir_name} was not created"
            assert target.is_dir(), f"{dir_name} exists but is not a directory"

    def test_no_error_if_dirs_exist(self, tmp_path, monkeypatch):
        """Verify that create_directories does not fail if directories already exist."""
        monkeypatch.chdir(tmp_path)
        
        # Pre-create one directory
        (tmp_path / "code").mkdir()
        
        # Should not raise an exception
        try:
            create_directories()
        except Exception as e:
            pytest.fail(f"create_directories raised an exception when directories existed: {e}")

    def test_nested_directories_created(self, tmp_path, monkeypatch):
        """Verify that nested directories (e.g., data/raw) are created correctly."""
        monkeypatch.chdir(tmp_path)
        
        create_directories()
        
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "results" / "figures").exists()
        assert (tmp_path / "data" / "processed").exists()
        assert (tmp_path / "results" / "tables").exists()
