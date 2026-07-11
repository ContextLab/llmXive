"""
Unit tests to verify the project structure exists.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code",
    "data",
    "tests",
    "state",
    "data/raw",
    "data/processed",
    "data/results",
    "specs",
    "contracts"
]

REQUIRED_FILES = [
    "code/__init__.py",
    "data/__init__.py",
    "tests/__init__.py",
    "state/__init__.py"
]

def test_required_directories_exist():
    """Verify all required directories exist."""
    for directory in REQUIRED_DIRS:
        assert os.path.isdir(directory), f"Missing directory: {directory}"

def test_required_files_exist():
    """Verify all required package init files exist."""
    for file_path in REQUIRED_FILES:
        assert os.path.isfile(file_path), f"Missing file: {file_path}"