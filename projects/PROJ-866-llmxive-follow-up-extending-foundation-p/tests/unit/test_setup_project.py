import os
import pytest
from pathlib import Path
import sys

# Add the parent directory to the path to allow imports from code/
# Assuming this test runs from the project root or tests/
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_project import create_structure

def test_create_structure_creates_directories(tmp_path):
    """
    Test that create_structure creates the required directory hierarchy.
    We run this in a temporary directory to avoid polluting the real project.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        created = create_structure()
        
        # Verify expected directories exist
        expected_dirs = [
            "code", "code/analysis", "code/engines", "code/generators", "code/utils",
            "data", "data/raw", "data/processed", "data/results",
            "tests", "tests/unit", "tests/integration", "tests/contract",
            "state", "state/projects"
        ]
        
        for rel_dir in expected_dirs:
            full_path = tmp_path / rel_dir
            assert full_path.exists(), f"Directory {rel_dir} was not created"
            assert full_path.is_dir(), f"{rel_dir} exists but is not a directory"
        
        # Verify we got the right count
        assert len(created) == len(expected_dirs)
        
    finally:
        os.chdir(original_cwd)

def test_create_structure_idempotent(tmp_path):
    """
    Test that running create_structure twice doesn't fail or duplicate.
    """
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        # First run
        first_run = create_structure()
        # Second run
        second_run = create_structure()
        
        # Should return empty list or same list if logic checks existence
        # In our implementation, it only returns newly created paths
        assert len(second_run) == 0, "Second run should not create new directories if they exist"
    finally:
        os.chdir(original_cwd)