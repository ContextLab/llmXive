"""
Tests for Project Initialization (T001).
Verifies directory structure and __init__.py creation.
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
  "code/models"
]

def test_required_directories_exist():
    """Verify that all required directories exist after T001 execution."""
    root = get_project_root()
    missing = []
    for dir_name in REQUIRED_DIRS:
        dir_path = root / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            missing.append(dir_name)
    
    assert not missing, f"Missing required directories: {', '.join(missing)}"

def test_init_files_exist():
    """Verify that __init__.py files exist in Python packages."""
    root = get_project_root()
    packages = [
        "code",
        "code/utils",
        "tests"
    ]
    
    for pkg in packages:
        pkg_path = root / pkg
        # Ensure the directory exists first (it should from T001)
        assert pkg_path.exists(), f"Package directory missing: {pkg}"
        
        init_file = pkg_path / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {pkg}"
        # Verify it's a valid file (can be empty)
        assert init_file.is_file(), f"{pkg}/__init__.py is not a file"

def test_code_models_directory_exists():
    """Specific check for code/models as per T001 requirements."""
    root = get_project_root()
    models_dir = root / "code" / "models"
    assert models_dir.exists(), "code/models directory is missing"
    assert models_dir.is_dir(), "code/models is not a directory"
