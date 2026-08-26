import os
import tempfile
import pytest
from pathlib import Path
import sys
from setup_project_structure import setup_directories

class TestProjectStructure:
    """
    Tests to verify that the project structure is correctly created.
    """

    def test_setup_directories_creates_folders(self, tmp_path):
        """Test that setup_directories creates all required directories."""
        # Change to temp directory for testing
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run the setup
            setup_directories()
            
            # Verify directories exist
            required_dirs = [
                "src", "tests", "data", "specs", "figures", "artifacts",
                "src/lib", "src/services", "src/models", "src/analysis", 
                "src/cli", "src/scripts",
                "tests/unit", "tests/integration",
                "data/raw", "data/derived", "data/gold_standard",
                "specs/001-gene-regulation", "specs/001-gene-regulation/contracts"
            ]
            
            for dir_name in required_dirs:
                dir_path = tmp_path / dir_name
                assert dir_path.exists(), f"Directory {dir_name} was not created"
                assert dir_path.is_dir(), f"{dir_name} exists but is not a directory"
        finally:
            os.chdir(original_cwd)

    def test_init_files_created(self, tmp_path):
        """Test that __init__.py files are created for Python packages."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_directories()
            
            init_files = [
                "src/__init__.py",
                "src/lib/__init__.py",
                "src/services/__init__.py",
                "src/models/__init__.py",
                "src/analysis/__init__.py",
                "src/cli/__init__.py",
                "src/scripts/__init__.py",
                "tests/__init__.py",
                "tests/unit/__init__.py",
                "tests/integration/__init__.py",
            ]
            
            for init_file in init_files:
                file_path = tmp_path / init_file
                assert file_path.exists(), f"Init file {init_file} was not created"
                assert file_path.is_file(), f"{init_file} exists but is not a file"
        finally:
            os.chdir(original_cwd)

    def test_data_subdirectories_exist(self, tmp_path):
        """Test that data directory has required subdirectories."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_directories()
            
            data_subdirs = ["raw", "derived", "gold_standard"]
            for subdir in data_subdirs:
                subdir_path = tmp_path / "data" / subdir
                assert subdir_path.exists(), f"Data subdirectory {subdir} was not created"
        finally:
            os.chdir(original_cwd)

    def test_specs_structure(self, tmp_path):
        """Test that specs directory has the required gene-regulation structure."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            setup_directories()
            
            specs_dirs = [
                "specs/001-gene-regulation",
                "specs/001-gene-regulation/contracts"
            ]
            
            for dir_path in specs_dirs:
                full_path = tmp_path / dir_path
                assert full_path.exists(), f"Specs directory {dir_path} was not created"
        finally:
            os.chdir(original_cwd)