import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_directories import initialize_project_structure

def test_initialize_project_structure_creates_dirs():
    """
    Test that initialize_project_structure creates the required directories.
    """
    # We assume the test runs from the project root or the script handles pathing
    # The script calculates project_root relative to itself.
    
    # Run the function
    created = initialize_project_structure()
    
    # Check that the function returns a list
    assert isinstance(created, list)
    
    # Verify the directories actually exist on disk
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "results"
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."
