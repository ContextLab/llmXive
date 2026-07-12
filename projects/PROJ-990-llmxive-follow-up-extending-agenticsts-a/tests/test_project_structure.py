"""
Basic test to verify the project directory structure exists.
"""
import os
from pathlib import Path
import pytest

# Determine the project root (parent of tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "models",
    "figures",
]

def test_required_directories_exist():
    """Assert that all required project directories exist."""
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing_dirs.append(dir_path)
    
    assert not missing_dirs, f"Missing required directories: {missing_dirs}"

def test_code_directory_is_writable():
    """Assert that the code directory is writable (sanity check)."""
    code_dir = PROJECT_ROOT / "code"
    assert os.access(code_dir, os.W_OK), f"Code directory is not writable: {code_dir}"