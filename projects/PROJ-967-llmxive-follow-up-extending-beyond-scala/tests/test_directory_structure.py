"""
Tests for verifying the project directory structure.

This test module ensures that the required directories for the llmXive project
are properly created and accessible.
"""
import os
import pytest
from pathlib import Path

# Get the project root (parent of the test directory's parent)
# Assuming test structure: tests/test_directory_structure.py
# Project root is: tests/../..
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "results"
]

@pytest.fixture
def project_root():
    """Provide the project root path."""
    return PROJECT_ROOT

def test_required_directories_exist(project_root):
    """Test that all required directories exist."""
    for dir_name in REQUIRED_DIRS:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory does not exist: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_data_raw_directory(project_root):
    """Test that data/raw directory exists."""
    dir_path = project_root / "data" / "raw"
    assert dir_path.exists()
    assert dir_path.is_dir()

def test_data_processed_directory(project_root):
    """Test that data/processed directory exists."""
    dir_path = project_root / "data" / "processed"
    assert dir_path.exists()
    assert dir_path.is_dir()

def test_code_directory(project_root):
    """Test that code directory exists."""
    dir_path = project_root / "code"
    assert dir_path.exists()
    assert dir_path.is_dir()

def test_tests_directory(project_root):
    """Test that tests directory exists."""
    dir_path = project_root / "tests"
    assert dir_path.exists()
    assert dir_path.is_dir()

def test_results_directory(project_root):
    """Test that results directory exists."""
    dir_path = project_root / "results"
    assert dir_path.exists()
    assert dir_path.is_dir()

def test_directory_permissions(project_root):
    """Test that directories are writable."""
    for dir_name in REQUIRED_DIRS:
        dir_path = project_root / dir_name
        # Check write permission by attempting to create a temp file
        test_file = dir_path / ".test_write_permission"
        try:
            test_file.touch()
            test_file.unlink()
        except OSError as e:
            pytest.fail(f"Directory not writable: {dir_path} - {e}")
