"""
Unit tests for the project setup script (T001).
Verifies that the required directory structure is created correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the main logic to test it in isolation
# We assume the script logic is in code/setup_directories.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import main

def test_directory_structure_creation(tmp_path):
    """
    Test that the script creates the expected directory structure.
    We patch the working directory to a temporary path to avoid polluting the real project.
    """
    # Save original cwd
    original_cwd = Path.cwd()
    
    try:
        # Change to temp directory
        os.chdir(tmp_path)
        
        # We need to mock the specific path logic since main() uses Path(".")
        # The main() function defines base_dir relative to current dir.
        # We will call main and check if the dirs exist in tmp_path/projects/...
        
        # Note: The main() function prints to stdout and returns 0.
        # We capture the return code.
        exit_code = main()
        
        assert exit_code == 0, "Setup script should return 0 on success"
        
        base_dir = tmp_path / "projects" / "PROJ-422-predicting-molecular-permeability-coeffi"
        
        expected_dirs = [
            "code/data",
            "code/models",
            "code/analysis",
            "data/raw",
            "data/processed",
            "data/interim",
            "results",
            "tests/unit",
            "tests/integration",
        ]
        
        for rel_path in expected_dirs:
            full_path = base_dir / rel_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} exists but is not a directory"
            
    finally:
        # Restore original cwd
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """
    Test that running the script twice does not cause errors (idempotent).
    """
    original_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        
        # Run first time
        exit_code_1 = main()
        assert exit_code_1 == 0
        
        # Run second time
        exit_code_2 = main()
        assert exit_code_2 == 0
        
    finally:
        os.chdir(original_cwd)