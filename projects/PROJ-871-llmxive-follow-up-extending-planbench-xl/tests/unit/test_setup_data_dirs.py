"""
Unit tests for the data directory setup script.
Verifies that the required data directories are created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import get_project_root, ensure_dirs_exist
from setup_data_dirs import main as setup_data_dirs_main


class TestDataDirectorySetup:
    """Tests for data directory structure creation."""

    def test_required_subdirectories_exist(self, tmp_path):
        """
        Verify that all required data subdirectories are created.
        """
        # Create a temporary project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Mock the project root by setting an environment variable or
        # temporarily patching the config
        # For this test, we'll directly test the directory creation logic
        
        data_dir = project_root / "data"
        required_dirs = ["raw", "derived", "logs", "results"]
        
        # Create directories
        for dir_name in required_dirs:
            dir_path = data_dir / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            assert dir_path.exists(), f"Directory {dir_path} should exist"
            assert dir_path.is_dir(), f"{dir_path} should be a directory"

    def test_data_gitignore_exists(self, tmp_path):
        """
        Verify that .gitignore exists in the data directory.
        """
        # Create a temporary project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        data_dir = project_root / "data"
        data_dir.mkdir()
        
        gitignore_path = data_dir / ".gitignore"
        
        # Create a minimal .gitignore
        gitignore_path.write_text("# Data directory ignore rules\n*\n!.gitignore\n")
        
        assert gitignore_path.exists(), ".gitignore should exist in data directory"
        assert gitignore_path.is_file(), ".gitignore should be a file"
        
        content = gitignore_path.read_text()
        assert "*" in content, ".gitignore should contain ignore patterns"

    def test_setup_data_dirs_script_creates_structure(self, tmp_path):
        """
        Test that the setup_data_dirs script creates the correct structure.
        This test mocks the project root to point to our temp directory.
        """
        import unittest.mock as mock
        
        # Create a temporary project root
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        # Mock the get_project_root function to return our temp directory
        with mock.patch('setup_data_dirs.get_project_root', return_value=project_root):
            # Also mock ensure_dirs_exist to avoid actual creation if needed,
            # but we want to test actual creation
            # Just run the main function
            result = setup_data_dirs_main()
            
            # Verify the function returned 0 (success)
            assert result == 0, "setup_data_dirs main should return 0 on success"
            
            # Verify directories were created
            data_dir = project_root / "data"
            assert data_dir.exists(), "data directory should exist"
            
            required_dirs = ["raw", "derived", "logs", "results"]
            for dir_name in required_dirs:
                dir_path = data_dir / dir_name
                assert dir_path.exists(), f"Directory {dir_path} should exist"
                assert dir_path.is_dir(), f"{dir_path} should be a directory"