"""
Unit tests for directory structure initialization.
Verifies that required directories exist after setup.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parents[2]

def test_code_directory_exists(project_root):
    """Test that the code directory exists."""
    code_dir = project_root / "code"
    assert code_dir.exists(), f"Directory 'code' does not exist at {code_dir}"
    assert code_dir.is_dir(), f"'code' is not a directory"

def test_tests_directory_exists(project_root):
    """Test that the tests directory exists."""
    tests_dir = project_root / "tests"
    assert tests_dir.exists(), f"Directory 'tests' does not exist at {tests_dir}"
    assert tests_dir.is_dir(), f"'tests' is not a directory"

def test_artifacts_directory_exists(project_root):
    """Test that the artifacts directory exists."""
    artifacts_dir = project_root / "artifacts"
    assert artifacts_dir.exists(), f"Directory 'artifacts' does not exist at {artifacts_dir}"
    assert artifacts_dir.is_dir(), f"'artifacts' is not a directory"

def test_data_directories_exist(project_root):
    """Test that data subdirectories exist."""
    data_subdirs = ["raw", "processed", "assets"]
    for subdir in data_subdirs:
        dir_path = project_root / "data" / subdir
        assert dir_path.exists(), f"Directory 'data/{subdir}' does not exist at {dir_path}"
        assert dir_path.is_dir(), f"'data/{subdir}' is not a directory"

def test_artifacts_subdirectories_exist(project_root):
    """Test that artifacts subdirectories exist."""
    artifacts_subdirs = ["logs", "metrics"]
    for subdir in artifacts_subdirs:
        dir_path = project_root / "artifacts" / subdir
        assert dir_path.exists(), f"Directory 'artifacts/{subdir}' does not exist at {dir_path}"
        assert dir_path.is_dir(), f"'artifacts/{subdir}' is not a directory"