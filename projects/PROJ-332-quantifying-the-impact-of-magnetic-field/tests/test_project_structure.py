"""
Test to verify the project structure has been correctly initialized.
Checks for the existence of required directories defined in plan.md.
"""
import os
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent


def test_code_directory_exists(project_root):
    """Test that the code/ directory exists."""
    code_dir = project_root / "code"
    assert code_dir.exists(), "code/ directory does not exist"
    assert code_dir.is_dir(), "code/ is not a directory"


def test_data_raw_directory_exists(project_root):
    """Test that the data/raw/ directory exists."""
    data_raw_dir = project_root / "data" / "raw"
    assert data_raw_dir.exists(), "data/raw/ directory does not exist"
    assert data_raw_dir.is_dir(), "data/raw/ is not a directory"


def test_data_processed_directory_exists(project_root):
    """Test that the data/processed/ directory exists."""
    data_processed_dir = project_root / "data" / "processed"
    assert data_processed_dir.exists(), "data/processed/ directory does not exist"
    assert data_processed_dir.is_dir(), "data/processed/ is not a directory"


def test_artifacts_directory_exists(project_root):
    """Test that the artifacts/ directory exists."""
    artifacts_dir = project_root / "artifacts"
    assert artifacts_dir.exists(), "artifacts/ directory does not exist"
    assert artifacts_dir.is_dir(), "artifacts/ is not a directory"


def test_tests_directory_exists(project_root):
    """Test that the tests/ directory exists."""
    tests_dir = project_root / "tests"
    assert tests_dir.exists(), "tests/ directory does not exist"
    assert tests_dir.is_dir(), "tests/ is not a directory"


def test_package_initialization(project_root):
    """Test that __init__.py files exist for Python packages."""
    required_init_files = [
        project_root / "code" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "data" / "__init__.py",
    ]
    
    for init_file in required_init_files:
        assert init_file.exists(), f"{init_file.relative_to(project_root)} does not exist"
        assert init_file.is_file(), f"{init_file.relative_to(project_root)} is not a file"