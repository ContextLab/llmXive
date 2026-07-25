"""
Test suite for project setup and directory verification.
"""
import os
import pytest
from pathlib import Path
from config import get_project_root

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "outputs",
    "tests",
    "state/projects",
    "code/models",
    "code/utils",
    "code/configs",
    "figures"
]

def test_required_directories_exist():
    """Verify that all required project directories exist."""
    project_root = get_project_root()
    missing = []
    
    for dir_path in REQUIRED_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    assert len(missing) == 0, f"Missing required directories: {missing}"

def test_init_files_exist():
    """Verify that __init__.py files exist in Python packages."""
    project_root = get_project_root()
    package_dirs = ["code", "tests", "code/utils", "code/configs"]
    
    for pkg_dir in package_dirs:
        init_file = project_root / pkg_dir / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py at {init_file}"

def test_directory_structure_is_valid():
    """Integration test: ensure the full directory structure is valid."""
    # This test runs the verification logic directly
    from verify_directories import verify_directories
    
    # Should not raise an exception
    try:
        verify_directories()
    except FileNotFoundError as e:
        pytest.fail(f"Directory verification failed: {e}")
