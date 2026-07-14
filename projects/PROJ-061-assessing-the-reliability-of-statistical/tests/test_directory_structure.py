"""
Test to verify the directory structure created by T009 exists.
"""
import os
from pathlib import Path

def test_required_directories_exist():
    """Verify that the required directories from T009 exist."""
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs",
    ]

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        assert full_path.exists(), f"Directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_init_files_exist():
    """Verify __init__.py files exist in Python packages."""
    base_dir = Path(__file__).resolve().parent.parent
    
    python_packages = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    for pkg_path in python_packages:
        full_path = base_dir / pkg_path
        init_file = full_path / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {full_path}"