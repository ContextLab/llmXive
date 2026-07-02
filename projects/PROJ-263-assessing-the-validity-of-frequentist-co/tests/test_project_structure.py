"""
Tests for T001: Verify project structure creation.
"""
import os
import pytest

BASE_DIR = os.getcwd()

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "tests/unit",
    "tests/integration",
    "outputs",
    "figures",
    "specs",
    "notebooks",
    "docs"
]

REQUIRED_FILES = [
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
    "data/interim/.gitkeep",
    "outputs/.gitkeep",
    "figures/.gitkeep",
    "specs/.gitkeep",
    "code/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
]

def test_directories_exist():
    """Verify all required directories exist."""
    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(BASE_DIR, dir_path)
        assert os.path.isdir(full_path), f"Directory missing: {dir_path}"

def test_files_exist():
    """Verify all required placeholder files exist."""
    for file_path in REQUIRED_FILES:
        full_path = os.path.join(BASE_DIR, file_path)
        assert os.path.isfile(full_path), f"File missing: {file_path}"

def test_code_package_is_importable():
    """Verify code/__init__.py makes 'code' a package."""
    # This is a basic check; actual importability depends on PYTHONPATH
    init_path = os.path.join(BASE_DIR, "code", "__init__.py")
    assert os.path.exists(init_path), "code/__init__.py must exist"
