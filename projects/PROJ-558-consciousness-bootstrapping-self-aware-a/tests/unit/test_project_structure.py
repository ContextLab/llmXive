"""
Unit tests for project structure creation.
Verifies that the required directories exist after running create_project_structure.py.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the function from the code module
# Since the script is in code/, we might need to adjust sys.path if running from tests/
import sys
from pathlib import Path

# Add the project root to path if necessary (assuming tests are run from root)
# The create_project_structure.py is in code/
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from create_project_structure import create_structure


class TestProjectStructure:
    """Tests for the project structure creation functionality."""

    def test_directory_creation(self, tmp_path):
        """Test that create_structure creates the required directories."""
        # Change to temporary directory to avoid cluttering the real project
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Create the structure
            created_paths = create_structure()
            
            # Define expected directories relative to tmp_path
            project_root = tmp_path / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
            
            expected_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "tests",
                "artifacts",
                "artifacts/checkpoints",
                "artifacts/results"
            ]
            
            # Verify each directory exists
            for subdir in expected_dirs:
                full_path = project_root / subdir
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"
            
            # Verify the function returns the correct paths
            assert len(created_paths) == len(expected_dirs)
            
        finally:
            os.chdir(original_cwd)

    def test_directories_are_non_empty_or_valid(self, tmp_path):
        """Test that created directories are valid (exist and are accessible)."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            create_structure()
            
            project_root = tmp_path / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
            
            # Check that we can list contents of each directory (even if empty)
            for subdir in ["data/raw", "data/processed", "code", "tests", 
                           "artifacts", "artifacts/checkpoints", "artifacts/results"]:
                dir_path = project_root / subdir
                # This should not raise an exception
                list(dir_path.iterdir())
                
        finally:
            os.chdir(original_cwd)

    def test_idempotency(self, tmp_path):
        """Test that running create_structure multiple times doesn't cause errors."""
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Run twice
            create_structure()
            create_structure()
            
            project_root = tmp_path / "projects" / "PROJ-558-consciousness-bootstrapping-self-aware-a"
            
            # Verify directories still exist
            assert (project_root / "code").exists()
            assert (project_root / "data/raw").exists()
            assert (project_root / "artifacts/results").exists()
            
        finally:
            os.chdir(original_cwd)