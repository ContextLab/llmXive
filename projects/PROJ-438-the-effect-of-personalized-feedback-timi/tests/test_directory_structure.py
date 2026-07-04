"""
Unit tests to verify the existence of required project directories.
"""
import os
import pathlib
import pytest

from conftest import PROJECT_ROOT

def test_tests_directory_exists():
    """Verify that the tests directory exists."""
    assert PROJECT_ROOT.exists(), "Project root does not exist"
    tests_dir = PROJECT_ROOT / "tests"
    assert tests_dir.exists(), f"Tests directory not found at {tests_dir}"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_data_directories_exist():
    """Verify that required data subdirectories exist."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/cache",
        "data/checksums"
    ]
    for rel_path in required_dirs:
        full_path = PROJECT_ROOT / rel_path
        assert full_path.exists(), f"Required directory missing: {full_path}"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_code_directory_exists():
    """Verify that the code directory exists."""
    code_dir = PROJECT_ROOT / "code"
    assert code_dir.exists(), f"Code directory not found at {code_dir}"
    assert code_dir.is_dir(), f"{code_dir} is not a directory"