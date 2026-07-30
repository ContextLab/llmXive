"""
Unit tests for the project setup script (T001).
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, 'code')
from setup_project import create_directories

class TestProjectStructure:
    """Tests for T001: Create project directory structure."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        required_dirs = [
            "code",
            "data",
            "data/raw_cif",
            "models",
            "results",
            "contracts",
            "specs"
        ]
        
        result = create_directories(str(tmp_path))
        
        # Check that all expected paths were reported as created (or existed)
        for dir_name in required_dirs:
            expected_path = tmp_path / dir_name
            assert expected_path.exists(), f"Directory {dir_name} was not created"
            assert expected_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_creates_nested_directories(self, tmp_path):
        """Verify that nested directories (e.g., data/raw_cif) are created."""
        result = create_directories(str(tmp_path))
        
        raw_cif_path = tmp_path / "data" / "raw_cif"
        assert raw_cif_path.exists(), "Nested directory data/raw_cif was not created"
        assert raw_cif_path.is_dir(), "data/raw_cif is not a directory"

    def test_idempotent_execution(self, tmp_path):
        """Verify that running the script twice doesn't cause errors."""
        # First run
        result1 = create_directories(str(tmp_path))
        
        # Second run
        result2 = create_directories(str(tmp_path))
        
        # All directories should still exist
        required_dirs = ["code", "data", "models", "results", "contracts", "specs"]
        for dir_name in required_dirs:
            assert (tmp_path / dir_name).exists()

    def test_returns_created_paths(self, tmp_path):
        """Verify that the function returns the list of created paths."""
        result = create_directories(str(tmp_path))
        
        assert isinstance(result, list), "Function should return a list of paths"
        assert len(result) > 0, "Function should return at least one created path"
        
        # Verify paths are absolute or relative to tmp_path
        for path_str in result:
            path_obj = Path(path_str)
            # If relative, it should resolve under tmp_path
            if not path_obj.is_absolute():
                assert (tmp_path / path_str).exists()

    def test_handles_existing_directories(self, tmp_path):
        """Verify that existing directories don't cause errors."""
        # Pre-create some directories
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        
        result = create_directories(str(tmp_path))
        
        # Should still succeed
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data").exists()
        # Other directories should also be created
        assert (tmp_path / "models").exists()