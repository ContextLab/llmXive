"""
Unit tests to verify the project directory structure is correctly created.
"""
import os
from pathlib import Path
import pytest

# Determine the project root (parent of the 'tests' directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_code_directory_exists():
    """Verify the main code directory exists."""
    code_dir = PROJECT_ROOT / "code"
    assert code_dir.exists(), f"Directory {code_dir} does not exist"
    assert code_dir.is_dir(), f"{code_dir} is not a directory"

def test_code_subdirectories_exist():
    """Verify all required code subdirectories exist."""
    required_subdirs = ["data", "inference", "scoring", "analysis", "utils"]
    for subdir in required_subdirs:
        path = PROJECT_ROOT / "code" / subdir
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

def test_data_directory_exists():
    """Verify the main data directory exists."""
    data_dir = PROJECT_ROOT / "data"
    assert data_dir.exists(), f"Directory {data_dir} does not exist"
    assert data_dir.is_dir(), f"{data_dir} is not a directory"

def test_data_subdirectories_exist():
    """Verify all required data subdirectories exist."""
    required_subdirs = ["raw", "processed", "gold"]
    for subdir in required_subdirs:
        path = PROJECT_ROOT / "data" / subdir
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

def test_tests_directory_exists():
    """Verify the main tests directory exists."""
    tests_dir = PROJECT_ROOT / "tests"
    assert tests_dir.exists(), f"Directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_tests_subdirectories_exist():
    """Verify all required tests subdirectories exist."""
    required_subdirs = ["unit", "integration"]
    for subdir in required_subdirs:
        path = PROJECT_ROOT / "tests" / subdir
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

def test_init_files_exist():
    """Verify __init__.py files exist in test directories."""
    init_paths = [
        PROJECT_ROOT / "tests" / "__init__.py",
        PROJECT_ROOT / "tests" / "unit" / "__init__.py",
        PROJECT_ROOT / "tests" / "integration" / "__init__.py",
    ]
    for path in init_paths:
        assert path.exists(), f"File {path} does not exist"
        assert path.is_file(), f"{path} is not a file"
