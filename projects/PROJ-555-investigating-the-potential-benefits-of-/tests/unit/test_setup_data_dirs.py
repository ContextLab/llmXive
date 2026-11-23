"""
Unit tests for the data directory setup script.
Verifies that the required directory structure and .gitkeep files are created.
"""
import os
import shutil
from pathlib import Path
import pytest

from setup_data_dirs import main


class TestDataDirectorySetup:
    """Test suite for data directory creation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Create a temporary test directory structure
        self.test_base = Path("test_data_temp")
        self.test_base.mkdir(exist_ok=True)
        
        # Patch the base directory for testing
        self.original_cwd = Path.cwd()
        
        yield
        
        # Cleanup
        if self.test_base.exists():
            shutil.rmtree(self.test_base)

    def test_main_creates_directories(self):
        """Test that main() creates the required directories."""
        # Run the main function
        main()
        
        # Verify directories exist
        expected_dirs = [
            "data/raw/landsat",
            "data/processed",
            "data/ecotourism"
        ]
        
        for dir_path in expected_dirs:
            full_path = Path(dir_path)
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_main_creates_gitkeep_files(self):
        """Test that main() creates .gitkeep files in each directory."""
        # Run the main function
        main()
        
        # Verify .gitkeep files exist
        expected_gitkeeps = [
            "data/raw/landsat/.gitkeep",
            "data/processed/.gitkeep",
            "data/ecotourism/.gitkeep"
        ]
        
        for file_path in expected_gitkeeps:
            full_path = Path(file_path)
            assert full_path.exists(), f"File {file_path} was not created"
            assert full_path.is_file(), f"{file_path} is not a file"

    def test_directory_structure_is_valid(self):
        """Test that the full directory tree structure is correct."""
        # Run the main function
        main()
        
        # Verify parent directories exist
        assert Path("data").exists()
        assert Path("data/raw").exists()
        
        # Verify specific subdirectories
        assert Path("data/raw/landsat").exists()
        assert Path("data/processed").exists()
        assert Path("data/ecotourism").exists()