import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add parent directory to path to import setup_project
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from setup_project import create_directories, create_init_files, check_structure

class TestSetupProject:
    """Unit tests for project setup functions."""

    def test_create_directories(self, tmp_path):
        """Test that create_directories creates all required folders."""
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            created = create_directories()
            
            # Check that all expected directories were created
            assert len(created) > 0
            
            # Verify specific directories exist
            expected_dirs = [
                "code/data_generation",
                "code/training",
                "data/raw",
                "tests/unit",
                "specs/001-predict-stiffness-cnn/contracts",
            ]
            
            for dir_path in expected_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_create_init_files(self, tmp_path):
        """Test that create_init_files creates __init__.py files."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # First create directories
            create_directories()
            created = create_init_files()
            
            # Check that init files were created
            assert len(created) > 0
            
            # Verify specific init files exist
            expected_inits = [
                "code/__init__.py",
                "code/data_generation/__init__.py",
                "tests/__init__.py",
            ]
            
            for file_path in expected_inits:
                full_path = tmp_path / file_path
                assert full_path.exists(), f"File {file_path} was not created"
                assert full_path.is_file(), f"{file_path} is not a file"
        finally:
            os.chdir(original_cwd)

    def test_check_structure(self, tmp_path):
        """Test that check_structure validates the project layout."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create the structure
            create_directories()
            create_init_files()
            
            # Check structure
            success, missing = check_structure()
            
            assert success, f"Structure check failed. Missing: {missing}"
            assert len(missing) == 0
        finally:
            os.chdir(original_cwd)

    def test_check_structure_missing(self, tmp_path):
        """Test that check_structure detects missing directories."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Only create some directories
            (tmp_path / "code").mkdir()
            (tmp_path / "code" / "data_generation").mkdir()
            
            # Check structure - should fail
            success, missing = check_structure()
            
            assert not success
            assert len(missing) > 0
            assert "code/training" in missing
        finally:
            os.chdir(original_cwd)