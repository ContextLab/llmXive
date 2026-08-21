"""
Test suite to verify that the required directories for T003 exist.
This test ensures the execution of setup_directories.py successfully
created 'explanations', 'state', and 'tests' directories.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = ["explanations", "state", "tests"]

@pytest.mark.parametrize("dir_name", REQUIRED_DIRS)
def test_directory_exists(dir_name: str) -> None:
    """
    Verify that a specific required directory exists in the project root.
    """
    project_root = Path(__file__).parent.parent
    target_path = project_root / dir_name
    
    assert target_path.exists(), f"Directory '{dir_name}' does not exist at {target_path}"
    assert target_path.is_dir(), f"Path '{dir_name}' is not a directory at {target_path}"

def test_all_required_directories_exist() -> None:
    """
    Verify that all required directories for T003 exist simultaneously.
    """
    project_root = Path(__file__).parent.parent
    missing = []
    
    for dir_name in REQUIRED_DIRS:
        target_path = project_root / dir_name
        if not target_path.exists() or not target_path.is_dir():
            missing.append(dir_name)
    
    assert not missing, f"Missing required directories: {missing}"