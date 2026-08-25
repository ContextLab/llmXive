"""
Unit tests to verify the project directory structure exists as expected.
"""
import os
import sys
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def test_code_directory_exists():
    """Test that the code/ directory exists."""
    project_root = get_project_root()
    code_dir = project_root / "code"
    assert code_dir.exists(), f"code/ directory does not exist at {code_dir}"
    assert code_dir.is_dir(), f"code/ is not a directory"

def test_data_raw_directory_exists():
    """Test that the data/raw/ directory exists."""
    project_root = get_project_root()
    data_raw_dir = project_root / "data" / "raw"
    assert data_raw_dir.exists(), f"data/raw/ directory does not exist at {data_raw_dir}"
    assert data_raw_dir.is_dir(), f"data/raw/ is not a directory"

def test_data_processed_directory_exists():
    """Test that the data/processed/ directory exists."""
    project_root = get_project_root()
    data_processed_dir = project_root / "data" / "processed"
    assert data_processed_dir.exists(), f"data/processed/ directory does not exist at {data_processed_dir}"
    assert data_processed_dir.is_dir(), f"data/processed/ is not a directory"

def test_tests_unit_directory_exists():
    """Test that the tests/unit/ directory exists."""
    project_root = get_project_root()
    tests_unit_dir = project_root / "tests" / "unit"
    assert tests_unit_dir.exists(), f"tests/unit/ directory does not exist at {tests_unit_dir}"
    assert tests_unit_dir.is_dir(), f"tests/unit/ is not a directory"

def test_tests_integration_directory_exists():
    """Test that the tests/integration/ directory exists."""
    project_root = get_project_root()
    tests_integration_dir = project_root / "tests" / "integration"
    assert tests_integration_dir.exists(), f"tests/integration/ directory does not exist at {tests_integration_dir}"
    assert tests_integration_dir.is_dir(), f"tests/integration/ is not a directory"

def test_all_required_directories_exist():
    """Test that all required project directories exist."""
    project_root = get_project_root()
    
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/unit",
        "tests/integration",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(dir_path)
    
    assert not missing_dirs, f"The following required directories are missing: {missing_dirs}"
