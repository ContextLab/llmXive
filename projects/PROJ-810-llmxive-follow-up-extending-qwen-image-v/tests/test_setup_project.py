"""
Tests for the setup_project module.
"""
import os
import tempfile
from pathlib import Path
import pytest

from setup_project import create_directory_structure


class TestSetupProject:
    """Test cases for the setup_project module."""

    def test_directory_structure_creation(self):
        """Test that the directory structure is created correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a mock project structure
            project_path = Path(tmp_dir) / "PROJ-810-llmxive-follow-up-extending-qwen-image-v"
            project_path.mkdir()
            
            # Temporarily change the base path logic by mocking
            original_cwd = os.getcwd()
            os.chdir(project_path)
            
            try:
                # Run the setup
                result_path = create_directory_structure()
                
                # Verify the project path
                assert result_path == project_path
                
                # Check that required directories exist
                required_dirs = [
                    "code",
                    "code/analysis",
                    "code/data",
                    "code/data/cache",
                    "code/models",
                    "code/utils",
                    "tests",
                    "tests/unit",
                    "tests/integration",
                    "data",
                    "data/results",
                    "data/manual",
                    "data/raw",
                    "data/interim",
                    "figures",
                    "specs",
                    "config"
                ]
                
                for dir_name in required_dirs:
                    dir_path = project_path / dir_name
                    assert dir_path.exists(), f"Directory {dir_name} was not created"
                    assert dir_path.is_dir(), f"{dir_name} is not a directory"
                
                # Check that __init__.py files were created
                init_files = [
                    "code/__init__.py",
                    "code/analysis/__init__.py",
                    "code/data/__init__.py",
                    "code/data/cache/__init__.py",
                    "code/models/__init__.py",
                    "code/utils/__init__.py",
                    "tests/__init__.py",
                    "tests/unit/__init__.py",
                    "tests/integration/__init__.py"
                ]
                
                for init_file in init_files:
                    init_path = project_path / init_file
                    assert init_path.exists(), f"__init__.py file {init_file} was not created"
                    assert init_path.is_file(), f"{init_file} is not a file"
                    
            finally:
                os.chdir(original_cwd)

    def test_idempotent_creation(self):
        """Test that running the setup multiple times doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "PROJ-810-llmxive-follow-up-extending-qwen-image-v"
            project_path.mkdir()
            
            original_cwd = os.getcwd()
            os.chdir(project_path)
            
            try:
                # Run setup twice
                result1 = create_directory_structure()
                result2 = create_directory_structure()
                
                assert result1 == result2 == project_path
            finally:
                os.chdir(original_cwd)