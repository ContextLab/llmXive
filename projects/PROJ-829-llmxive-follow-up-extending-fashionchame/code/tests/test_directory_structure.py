import os
import sys
from pathlib import Path
import pytest

# The root of the project is the parent of the 'code' directory
root_dir = Path(__file__).resolve().parent.parent

def test_code_directory_exists():
    """Verify that the 'code' directory exists at the repository root."""
    code_path = root_dir / "code"
    assert code_path.exists(), f"Directory {code_path} does not exist"
    assert code_path.is_dir(), f"{code_path} is not a directory"

def test_data_raw_directory_exists():
    """Verify that 'data/raw' directory exists."""
    data_raw_path = root_dir / "data" / "raw"
    assert data_raw_path.exists(), f"Directory {data_raw_path} does not exist"
    assert data_raw_path.is_dir(), f"{data_raw_path} is not a directory"

def test_data_processed_directory_exists():
    """Verify that 'data/processed' directory exists."""
    data_processed_path = root_dir / "data" / "processed"
    assert data_processed_path.exists(), f"Directory {data_processed_path} does not exist"
    assert data_processed_path.is_dir(), f"{data_processed_path} is not a directory"

def test_tests_unit_directory_exists():
    """Verify that 'tests/unit' directory exists."""
    tests_unit_path = root_dir / "tests" / "unit"
    assert tests_unit_path.exists(), f"Directory {tests_unit_path} does not exist"
    assert tests_unit_path.is_dir(), f"{tests_unit_path} is not a directory"

def test_tests_integration_directory_exists():
    """Verify that 'tests/integration' directory exists."""
    tests_integration_path = root_dir / "tests" / "integration"
    assert tests_integration_path.exists(), f"Directory {tests_integration_path} does not exist"
    assert tests_integration_path.is_dir(), f"{tests_integration_path} is not a directory"

def test_all_required_directories_exist():
    """
    High-level test to verify all required directories from T001 are present.
    """
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
    ]
    
    missing = []
    for rel_path in required_dirs:
        full_path = root_dir / rel_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(rel_path)
    
    assert not missing, f"The following required directories are missing: {missing}"
