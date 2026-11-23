"""
Test to verify T001: Project structure creation.
Ensures all required directories and __init__.py files exist.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "code/tests",
    "specs/001-symbolic-memory-edge-robotics/contracts",
    "tests/unit",
    "tests/integration",
]

REQUIRED_INIT_DIRS = [
    "code",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "code/tests",
    "specs/001-symbolic-memory-edge-robotics/contracts",
    "tests/unit",
    "tests/integration",
]

def test_required_directories_exist():
    """Verify all required directories are present."""
    root = Path(".")
    for d in REQUIRED_DIRS:
        dir_path = root / d
        assert dir_path.exists(), f"Directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Not a directory: {dir_path}"

def test_init_files_exist():
    """Verify __init__.py files exist in required locations."""
    root = Path(".")
    for d in REQUIRED_INIT_DIRS:
        dir_path = root / d
        init_file = dir_path / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in: {dir_path}"
        # Ensure it's a file
        assert init_file.is_file(), f"Not a file: {init_file}"