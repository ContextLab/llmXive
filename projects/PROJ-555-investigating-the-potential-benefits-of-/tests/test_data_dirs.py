"""
Tests for data directory structure creation (Task T008).
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

from setup_data_dirs import main, create_gitkeep


class TestDataDirectoryCreation:
    """Test cases for data directory creation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Create a temporary directory structure for testing."""
        # Save current working directory
        self.original_cwd = Path.cwd()
        
        # Create a temporary directory and set it as cwd
        self.temp_dir = Path(tempfile.mkdtemp())
        os.chdir(self.temp_dir)
        
        yield
        
        # Restore original working directory
        os.chdir(self.original_cwd)
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    def test_directories_created(self):
        """Test that all required directories are created."""
        main()
        
        expected_dirs = [
            Path("data/raw/landsat"),
            Path("data/processed"),
            Path("data/ecotourism"),
        ]
        
        for dir_path in expected_dirs:
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_gitkeep_files_created(self):
        """Test that .gitkeep files are created in all directories."""
        main()
        
        expected_dirs = [
            Path("data/raw/landsat"),
            Path("data/processed"),
            Path("data/ecotourism"),
        ]
        
        for dir_path in expected_dirs:
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep not found in {dir_path}"
            assert gitkeep.is_file(), f"{gitkeep} is not a file"

    def test_create_gitkeep_idempotent(self):
        """Test that creating .gitkeep multiple times doesn't cause errors."""
        # Create directory first
        test_dir = Path("data/test_dir")
        test_dir.mkdir(parents=True)
        
        # Create .gitkeep twice
        create_gitkeep(test_dir)
        create_gitkeep(test_dir)
        
        gitkeep = test_dir / ".gitkeep"
        assert gitkeep.exists()
        # File should still exist and be a single file
        assert gitkeep.is_file()