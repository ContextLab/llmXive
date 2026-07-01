import pytest
import os
from pathlib import Path
import sys

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.setup_directories import create_directories

def test_create_directories_exists():
    """
    Test that create_directories creates the expected subdirectories
    under the code/ folder.
    """
    # We run the function which creates dirs relative to project root
    created = create_directories()
    
    # Verify the directories actually exist on disk
    base_path = Path(__file__).resolve().parent.parent
    
    expected_dirs = [
        "code/data",
        "code/models",
        "code/analysis"
    ]
    
    for dir_name in expected_dirs:
        full_path = base_path / dir_name
        assert full_path.exists(), f"Directory {full_path} was not created."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_create_directories_idempotent():
    """
    Test that running create_directories again does not raise errors
    and handles existing directories gracefully.
    """
    # Run twice
    result1 = create_directories()
    result2 = create_directories()
    
    # The function should not crash on the second run
    assert isinstance(result1, list)
    assert isinstance(result2, list)