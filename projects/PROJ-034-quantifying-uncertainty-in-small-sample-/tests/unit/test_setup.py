"""
Unit tests for the project setup script (T001).
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code', 'scripts'))
from setup_project_structure import create_directories

def test_create_directories():
    """Test that create_directories creates the expected folders."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the setup function
            result = create_directories()
            
            # Verify the function returned True
            assert result is True, "create_directories should return True on success"
            
            # Define expected directories
            expected_dirs = [
                "code/simulation",
                "code/models",
                "code/metrics",
                "code/validation",
                "code/plots",
                "code/scripts",
                "data/raw",
                "data/simulated",
                "data/results",
                "tests/unit",
                "tests/integration",
                "docs/paper"
            ]
            
            # Verify each directory exists
            for dir_path in expected_dirs:
                full_path = Path(tmp_dir) / dir_path
                assert full_path.exists(), f"Directory {dir_path} should exist"
                assert full_path.is_dir(), f"{dir_path} should be a directory"
            
            # Verify .gitkeep files exist in data directories
            gitkeep_dirs = ["data/raw", "data/simulated", "data/results"]
            for dir_path in gitkeep_dirs:
                gitkeep_path = Path(tmp_dir) / dir_path / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep should exist in {dir_path}"
                assert gitkeep_path.is_file(), f"{dir_path}/.gitkeep should be a file"
                
        finally:
            os.chdir(original_cwd)

def test_create_directories_idempotent():
    """Test that running create_directories twice doesn't fail."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run twice
            create_directories()
            result_second = create_directories()
            
            # Should still return True
            assert result_second is True
            
        finally:
            os.chdir(original_cwd)