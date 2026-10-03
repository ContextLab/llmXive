"""
Test suite for T001a: Directory Structure Creation.

Verifies that the setup script creates the required directories
and that they are actually directories.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile
import sys

# Add parent to path to import the script if needed, 
# though we will test the logic directly here.
sys.path.insert(0, str(Path(__file__).parent.parent))

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "tests",
    "state",
    "code/models",
    "code/utils",
    "code/simulations",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def test_directories_exist_after_setup(tmp_path):
    """
    Verify that running the setup logic creates all required directories.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Import the logic from the script
        from setup_structure import create_directories
        
        # Run the creation
        created = create_directories()
        
        # Verify all required dirs exist
        for rel_dir in REQUIRED_DIRS:
            full_path = tmp_path / rel_dir
            assert full_path.exists(), f"Directory missing: {full_path}"
            assert full_path.is_dir(), f"Path is not a directory: {full_path}"
        
        # Verify the function returned the list of created paths
        assert len(created) > 0, "Expected at least one directory to be created"
        
    finally:
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """
    Verify that running the setup script twice does not raise errors.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        from setup_structure import create_directories
        
        # Run twice
        first_run = create_directories()
        second_run = create_directories()
        
        # Second run should create nothing new
        assert len(second_run) == 0, "Idempotency failed: second run created directories"
        
    finally:
        os.chdir(original_cwd)
