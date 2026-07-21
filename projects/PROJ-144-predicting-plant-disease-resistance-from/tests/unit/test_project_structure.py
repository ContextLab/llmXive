import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """Verify that the core project directories exist."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "state"
    ]
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        assert full_path.exists(), f"Required directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"

def test_code_subdirectories_exist():
    """Verify code subdirectories."""
    subdirs = [
        "code/data",
        "code/utils",
        "code/modeling"
    ]
    for sub in subdirs:
        full_path = Path(sub)
        assert full_path.exists(), f"Missing code subdir: {full_path}"

def test_test_subdirectories_exist():
    """Verify test subdirectories."""
    subdirs = [
        "tests/unit",
        "tests/integration"
    ]
    for sub in subdirs:
        full_path = Path(sub)
        assert full_path.exists(), f"Missing test subdir: {full_path}"