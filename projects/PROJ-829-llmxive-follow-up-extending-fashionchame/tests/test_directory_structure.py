"""
Tests to verify the project directory structure.

These tests ensure that required directories exist at the repository root.
"""
import os
import sys
from pathlib import Path
import pytest

# Get the project root (parent of tests directory)
PROJECT_ROOT = Path(__file__).parent.parent


def test_code_directory_exists():
    """Verify that the code/ directory exists at the repository root."""
    code_dir = PROJECT_ROOT / "code"
    assert code_dir.exists(), f"code/ directory not found at {code_dir}"
    assert code_dir.is_dir(), f"code/ is not a directory"


def test_data_directory_exists():
    """Verify that the data/ directory exists at the repository root."""
    data_dir = PROJECT_ROOT / "data"
    assert data_dir.exists(), f"data/ directory not found at {data_dir}"
    assert data_dir.is_dir(), f"data/ is not a directory"


def test_data_raw_directory_exists():
    """Verify that the data/raw/ directory exists."""
    data_raw_dir = PROJECT_ROOT / "data" / "raw"
    assert data_raw_dir.exists(), f"data/raw/ directory not found at {data_raw_dir}"
    assert data_raw_dir.is_dir(), f"data/raw/ is not a directory"


def test_data_processed_directory_exists():
    """Verify that the data/processed/ directory exists."""
    data_processed_dir = PROJECT_ROOT / "data" / "processed"
    assert data_processed_dir.exists(), f"data/processed/ directory not found at {data_processed_dir}"
    assert data_processed_dir.is_dir(), f"data/processed/ is not a directory"


def test_tests_unit_directory_exists():
    """Verify that the tests/unit/ directory exists."""
    tests_unit_dir = PROJECT_ROOT / "tests" / "unit"
    assert tests_unit_dir.exists(), f"tests/unit/ directory not found at {tests_unit_dir}"
    assert tests_unit_dir.is_dir(), f"tests/unit/ is not a directory"


def test_tests_integration_directory_exists():
    """Verify that the tests/integration/ directory exists."""
    tests_integration_dir = PROJECT_ROOT / "tests" / "integration"
    assert tests_integration_dir.exists(), f"tests/integration/ directory not found at {tests_integration_dir}"
    assert tests_integration_dir.is_dir(), f"tests/integration/ is not a directory"


def test_all_required_directories_exist():
    """Verify that all required directories exist."""
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        pytest.fail(f"Missing required directories: {', '.join(missing_dirs)}")
