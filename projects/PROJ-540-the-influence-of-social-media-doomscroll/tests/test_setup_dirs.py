"""
Tests for directory setup functionality.
"""
import os
import pytest
from pathlib import Path
from code.setup_dirs import create_directories

class TestSetupDirs:
    """Test cases for directory creation logic."""

    def test_required_directories_exist(self, tmp_path):
        """Verify that all required directories are created."""
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "outputs",
            "tests",
            "projects/PROJ-540-the-influence-of-social-media-doomscroll"
        ]
        
        create_directories(str(tmp_path))
        
        for dir_path in required_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_init_files_created(self, tmp_path):
        """Verify that __init__.py files are created in package directories."""
        package_dirs = [
            "code",
            "tests",
            "projects/PROJ-540-the-influence-of-social-media-doomscroll"
        ]
        
        create_directories(str(tmp_path))
        
        for pkg_dir in package_dirs:
            init_file = tmp_path / pkg_dir / "__init__.py"
            assert init_file.exists(), f"__init__.py not found in {pkg_dir}"
            assert init_file.is_file(), f"{init_file} exists but is not a file"

    def test_gitkeep_files_created(self, tmp_path):
        """Verify that .gitkeep files are created in data directories."""
        data_dirs = ["data/raw", "data/processed"]
        
        create_directories(str(tmp_path))
        
        for data_dir in data_dirs:
            keep_file = tmp_path / data_dir / ".gitkeep"
            assert keep_file.exists(), f".gitkeep not found in {data_dir}"
            assert keep_file.is_file(), f"{keep_file} exists but is not a file"

    def test_idempotency(self, tmp_path):
        """Verify that running create_directories twice does not cause errors."""
        create_directories(str(tmp_path))
        # Running again should not raise
        create_directories(str(tmp_path))
        
        # Verify directories still exist
        assert (tmp_path / "code").exists()
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "outputs").exists()