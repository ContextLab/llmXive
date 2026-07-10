"""
Unit tests to verify the project directory structure has been created correctly.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "utils",
    "artifacts",
    "artifacts/models",
    "artifacts/metrics",
    "artifacts/plots",
    "specs",
    "docs",
]

def test_required_directories_exist():
    """Assert that all required project directories exist."""
    missing_dirs = []
    for dir_path in REQUIRED_DIRS:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)
    
    assert not missing_dirs, f"The following directories are missing: {missing_dirs}"

def test_data_raw_is_empty_or_exists():
    """Assert data/raw exists (content check is for later tasks)."""
    assert os.path.isdir("data/raw")

def test_code_utils_exists():
    """Assert code/utils exists for utility modules."""
    assert os.path.isdir("code/utils")
