"""
Tests for T002: Project structure creation.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
# Since the script is in code/setup_project_structure.py, we need to adjust sys.path
import sys
import importlib.util

# Add the parent directory of 'code' to sys.path to import the module
# Assuming tests are in 'tests/' and script is in 'code/'
code_parent = Path(__file__).parent.parent
sys.path.insert(0, str(code_parent))

from setup_project_structure import create_directories


def test_create_directories_creates_folders():
    """Verify that create_directories creates code/, tests/, data/."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run the function
            created = create_directories()
            
            # Verify the returned list contains the expected paths
            assert len(created) == 3
            
            # Verify directories actually exist on disk
            assert os.path.isdir("code")
            assert os.path.isdir("tests")
            assert os.path.isdir("data")
            
        finally:
            os.chdir(original_cwd)


def test_create_directories_idempotent():
    """Verify that running create_directories twice doesn't fail."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_dir)
            
            # Run twice
            create_directories()
            create_directories()
            
            # Should still exist
            assert os.path.isdir("code")
            assert os.path.isdir("tests")
            assert os.path.isdir("data")
            
        finally:
            os.chdir(original_cwd)