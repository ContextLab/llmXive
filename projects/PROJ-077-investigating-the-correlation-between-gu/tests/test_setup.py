import os
from pathlib import Path
import pytest
from config import ensure_directories, PROJECT_ROOT

def test_directories_created():
    """
    Test that the setup process creates the required directories.
    """
    ensure_directories()
    
    required_dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "tests"
    ]
    
    for dir_path in required_dirs:
        assert dir_path.exists(), f"Directory {dir_path} was not created."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."