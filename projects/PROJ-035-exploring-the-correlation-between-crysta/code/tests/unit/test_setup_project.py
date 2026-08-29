"""
Unit tests for the project setup functionality.
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
from setup_project import setup_project_structure

class TestSetupProject:
    """Test cases for setup_project_structure function."""
    
    def test_creates_required_directories(self, tmp_path):
        """Test that all required directories are created."""
        # Change to temporary directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_project_structure()
            
            # Verify required directories exist
            required_dirs = [
                "src",
                "tests",
                "data/raw",
                "data/cleaned",
                "data/results",
                "figures",
                "contracts"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} is not a directory"
        finally:
            os.chdir(original_cwd)
    
    def test_creates_package_init_files(self, tmp_path):
        """Test that __init__.py files are created for Python packages."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_project_structure()
            
            # Verify __init__.py files exist for key packages
            package_inits = [
                "src/__init__.py",
                "tests/__init__.py",
                "src/utils/__init__.py",
                "src/ingest/__init__.py"
            ]
            
            for init_file in package_inits:
                file_path = tmp_path / init_file
                assert file_path.exists(), f"Package init file {init_file} was not created"
                assert file_path.is_file(), f"{init_file} is not a file"
        finally:
            os.chdir(original_cwd)
    
    def test_idempotent_execution(self, tmp_path):
        """Test that running the setup twice doesn't cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run setup twice
            result1 = setup_project_structure()
            result2 = setup_project_structure()
            
            assert result1 is True, "First setup run failed"
            assert result2 is True, "Second setup run failed"
            
            # Verify directories still exist
            assert (tmp_path / "src").exists()
            assert (tmp_path / "data/raw").exists()
        finally:
            os.chdir(original_cwd)
    
    def test_nested_directories_created(self, tmp_path):
        """Test that nested directories like data/raw are created correctly."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_project_structure()
            
            # Verify nested structure
            nested_dirs = [
                "data/raw",
                "data/cleaned",
                "data/results"
            ]
            
            for dir_name in nested_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Nested directory {dir_name} was not created"
                # Verify parent exists
                assert dir_path.parent.exists(), f"Parent of {dir_name} does not exist"
        finally:
            os.chdir(original_cwd)