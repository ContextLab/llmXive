import os
import pytest
from pathlib import Path
from code.setup_structure import create_project_structure

def test_create_project_structure():
    """
    Test that create_project_structure creates all required directories.
    This verifies T001 implementation.
    """
    # Get the project root (parent of code/)
    current_file = Path(__file__).parent
    project_root = current_file.parent
    
    # Run the function
    created = create_project_structure()
    
    # Verify all expected directories exist
    expected_dirs = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/tests",
        "artifacts/figures",
        "artifacts/reports",
        "state"
    ]
    
    for expected_dir in expected_dirs:
        dir_path = project_root / expected_dir
        assert dir_path.exists(), f"Directory {expected_dir} was not created"
        assert dir_path.is_dir(), f"{expected_dir} is not a directory"
    
    # Verify the function returned the correct list
    assert len(created) == len(expected_dirs)
    for dir_str in created:
        assert dir_str in expected_dirs, f"Unexpected directory in return: {dir_str}"

def test_directory_persistence():
    """
    Test that running create_project_structure again doesn't fail.
    """
    # Run twice to ensure idempotency
    create_project_structure()
    create_project_structure()
    
    # Verify directories still exist
    project_root = Path(__file__).parent.parent
    expected_dirs = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/tests",
        "artifacts/figures",
        "artifacts/reports",
        "state"
    ]
    
    for expected_dir in expected_dirs:
        dir_path = project_root / expected_dir
        assert dir_path.exists(), f"Directory {expected_dir} missing after second run"