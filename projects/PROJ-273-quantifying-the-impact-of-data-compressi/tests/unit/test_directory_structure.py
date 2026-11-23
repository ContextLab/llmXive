"""
Unit tests to verify the test directory structure exists as required by T007.
"""
import os
from pathlib import Path

def test_tests_root_exists():
    """Verify the tests/ root directory exists."""
    tests_root = Path(__file__).parent.parent
    assert tests_root.exists(), "tests/ directory does not exist"
    assert tests_root.is_dir(), "tests/ is not a directory"

def test_unit_directory_exists():
    """Verify tests/unit/ directory exists."""
    unit_dir = Path(__file__).parent
    assert unit_dir.exists(), "tests/unit/ directory does not exist"
    assert unit_dir.is_dir(), "tests/unit/ is not a directory"

def test_integration_directory_exists():
    """Verify tests/integration/ directory exists."""
    tests_root = Path(__file__).parent.parent
    integration_dir = tests_root / "integration"
    assert integration_dir.exists(), "tests/integration/ directory does not exist"
    assert integration_dir.is_dir(), "tests/integration/ is not a directory"

def test_contract_directory_exists():
    """Verify tests/contract/ directory exists."""
    tests_root = Path(__file__).parent.parent
    contract_dir = tests_root / "contract"
    assert contract_dir.exists(), "tests/contract/ directory does not exist"
    assert contract_dir.is_dir(), "tests/contract/ is not a directory"

def test_data_directory_structure():
    """Verify the expected __init__.py files exist in test subdirectories."""
    tests_root = Path(__file__).parent.parent
    expected_files = [
        tests_root / "__init__.py",
        tests_root / "unit" / "__init__.py",
        tests_root / "integration" / "__init__.py",
        tests_root / "contract" / "__init__.py",
        tests_root / "conftest.py"
    ]
    for f in expected_files:
        assert f.exists(), f"Required file {f} is missing"