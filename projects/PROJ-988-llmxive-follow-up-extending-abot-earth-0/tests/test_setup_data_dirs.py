"""
Unit tests for setup_data_dirs.py to verify directory structure creation.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path to import the module
sys_path_backup = list(os.sys.path)
try:
    current_dir = Path(__file__).resolve().parent.parent
    os.sys.path.insert(0, str(current_dir / "code"))
    from setup_data_dirs import create_directory_structure
finally:
    os.sys.path[:] = sys_path_backup


class TestDirectoryCreation:
    """Test cases for directory creation functionality."""

    def test_creates_core_directories(self, tmp_path):
        """Verify that core directories (code, data, tests, docs) are created."""
        create_directory_structure(tmp_path)
        
        assert (tmp_path / "code").is_dir()
        assert (tmp_path / "data").is_dir()
        assert (tmp_path / "tests").is_dir()
        assert (tmp_path / "docs").is_dir()

    def test_creates_data_subdirectories(self, tmp_path):
        """Verify that data subdirectories (raw, processed, results, interim) are created."""
        create_directory_structure(tmp_path)
        
        assert (tmp_path / "data" / "raw").is_dir()
        assert (tmp_path / "data" / "processed").is_dir()
        assert (tmp_path / "data" / "results").is_dir()
        assert (tmp_path / "data" / "interim").is_dir()

    def test_creates_code_subdirectories(self, tmp_path):
        """Verify that code subdirectories (lib, scripts) are created."""
        create_directory_structure(tmp_path)
        
        assert (tmp_path / "code" / "lib").is_dir()
        assert (tmp_path / "code" / "scripts").is_dir()

    def test_creates_test_subdirectories(self, tmp_path):
        """Verify that test subdirectories (unit, integration, fixtures) are created."""
        create_directory_structure(tmp_path)
        
        assert (tmp_path / "tests" / "unit").is_dir()
        assert (tmp_path / "tests" / "integration").is_dir()
        assert (tmp_path / "tests" / "fixtures").is_dir()

    def test_creates_docs_subdirectories(self, tmp_path):
        """Verify that docs subdirectories (api, user_guide, design) are created."""
        create_directory_structure(tmp_path)
        
        assert (tmp_path / "docs" / "api").is_dir()
        assert (tmp_path / "docs" / "user_guide").is_dir()
        assert (tmp_path / "docs" / "design").is_dir()

    def test_idempotent_creation(self, tmp_path):
        """Verify that running the function twice doesn't cause errors."""
        create_directory_structure(tmp_path)
        # Run again
        create_directory_structure(tmp_path)
        
        # All directories should still exist
        assert (tmp_path / "code").is_dir()
        assert (tmp_path / "data").is_dir()
        assert (tmp_path / "tests").is_dir()
        assert (tmp_path / "docs").is_dir()

    def test_nested_directory_creation(self, tmp_path):
        """Verify that nested directories are created correctly."""
        create_directory_structure(tmp_path)
        
        # Check a deeply nested path
        deep_path = tmp_path / "data" / "processed" / "patches_100m2"
        # We don't create this specific one in setup, but we verify the parent exists
        assert (tmp_path / "data" / "processed").is_dir()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])