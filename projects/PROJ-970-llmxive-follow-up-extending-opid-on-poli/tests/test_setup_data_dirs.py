"""
Tests for the directory setup script.
Verifies that the required directory structure is created correctly.
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_dirs import create_directories

class TestDirectorySetup:
    """Test cases for directory creation functionality."""

    def test_directories_created_in_temp_location(self, tmp_path):
        """Test that directories are created correctly in a temporary location."""
        # Save original cwd
        original_cwd = os.getcwd()
        
        try:
            # Create a temporary directory to act as project root
            test_project_root = tmp_path / "test_project"
            test_project_root.mkdir()
            
            # Create the 'code' directory inside the temp project
            code_dir = test_project_root / "code"
            code_dir.mkdir()
            
            # Change to the code directory so the script can find the project root
            os.chdir(str(code_dir))
            
            # Mock the project root detection by patching the function
            # We'll test by directly calling create_directories and checking results
            results = create_directories()
            
            # Verify that all expected directories were created
            expected_dirs = [
                "src",
                "src/environment",
                "src/agent",
                "src/simulation",
                "src/analysis",
                "tests",
                "data/raw/synthetic_graphs",
                "data/processed"
            ]
            
            for dir_name in expected_dirs:
                full_path = os.path.join(str(test_project_root), dir_name)
                assert os.path.exists(full_path), f"Directory {dir_name} was not created"
                assert os.path.isdir(full_path), f"{dir_name} exists but is not a directory"
            
            # Verify the results list contains the expected paths
            assert len(results) == len(expected_dirs), f"Expected {len(expected_dirs)} results, got {len(results)}"
            
        finally:
            # Restore original cwd
            os.chdir(original_cwd)

    def test_directories_exist_after_creation(self, tmp_path):
        """Test that directories persist after creation."""
        original_cwd = os.getcwd()
        
        try:
            test_project_root = tmp_path / "test_project"
            test_project_root.mkdir()
            code_dir = test_project_root / "code"
            code_dir.mkdir()
            os.chdir(str(code_dir))
            
            # Create directories
            create_directories()
            
            # Verify specific nested directories
            assert os.path.exists(os.path.join(str(test_project_root), "src/environment"))
            assert os.path.exists(os.path.join(str(test_project_root), "data/raw/synthetic_graphs"))
            assert os.path.exists(os.path.join(str(test_project_root), "data/processed"))
            
        finally:
            os.chdir(original_cwd)

    def test_idempotent_creation(self, tmp_path):
        """Test that running the script twice doesn't cause errors."""
        original_cwd = os.getcwd()
        
        try:
            test_project_root = tmp_path / "test_project"
            test_project_root.mkdir()
            code_dir = test_project_root / "code"
            code_dir.mkdir()
            os.chdir(str(code_dir))
            
            # Run twice
            results1 = create_directories()
            results2 = create_directories()
            
            # Both runs should succeed
            assert len(results1) > 0
            assert len(results2) > 0
            
        finally:
            os.chdir(original_cwd)