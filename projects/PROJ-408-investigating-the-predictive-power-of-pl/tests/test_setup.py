"""
Test for T001b: Verify project directory structure exists.
"""
import os
import pytest
from pathlib import Path

def test_project_directories_exist():
    """Verify all required directories from T001a/T001b exist."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "output/figures",
        "output/reports",
        "tests",
        "tests/contract/schemas",
        "state/projects",
        "docs"
    ]
    
    project_root = Path.cwd()
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_data_raw_is_writable():
    """Verify data/raw is writable (basic permission check)."""
    test_file = Path.cwd() / "data/raw" / ".test_write_permission"
    try:
        test_file.touch()
        test_file.unlink()
    except OSError:
        pytest.fail("data/raw directory is not writable")