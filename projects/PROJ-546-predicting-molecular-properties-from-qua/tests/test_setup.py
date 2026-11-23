"""
Basic setup tests to verify the project directory structure.

These tests ensure that the required directories for the project exist:
- tests/unit/
- tests/integration/
- tests/contract/
- docs/
"""
import os
import pytest
from pathlib import Path

# Get the project root (two levels up from this test file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_directory_structure_exists():
    """Test that the tests directory exists."""
    tests_dir = PROJECT_ROOT / "tests"
    assert tests_dir.exists(), f"tests/ directory does not exist at {tests_dir}"
    assert tests_dir.is_dir(), "tests/ is not a directory"

def test_unit_directory_exists():
    """Test that the unit test directory exists."""
    unit_dir = PROJECT_ROOT / "tests" / "unit"
    assert unit_dir.exists(), f"tests/unit/ directory does not exist at {unit_dir}"
    assert unit_dir.is_dir(), "tests/unit/ is not a directory"

def test_integration_directory_exists():
    """Test that the integration test directory exists."""
    integration_dir = PROJECT_ROOT / "tests" / "integration"
    assert integration_dir.exists(), f"tests/integration/ directory does not exist at {integration_dir}"
    assert integration_dir.is_dir(), "tests/integration/ is not a directory"

def test_contract_directory_exists():
    """Test that the contract test directory exists."""
    contract_dir = PROJECT_ROOT / "tests" / "contract"
    assert contract_dir.exists(), f"tests/contract/ directory does not exist at {contract_dir}"
    assert contract_dir.is_dir(), "tests/contract/ is not a directory"

def test_docs_directory_exists():
    """Test that the docs directory exists."""
    docs_dir = PROJECT_ROOT / "docs"
    assert docs_dir.exists(), f"docs/ directory does not exist at {docs_dir}"
    assert docs_dir.is_dir(), "docs/ is not a directory"

def test_test_init_files_exist():
    """Test that __init__.py files exist in test directories."""
    init_files = [
        PROJECT_ROOT / "tests" / "__init__.py",
        PROJECT_ROOT / "tests" / "unit" / "__init__.py",
        PROJECT_ROOT / "tests" / "integration" / "__init__.py",
        PROJECT_ROOT / "tests" / "contract" / "__init__.py",
    ]

    for init_file in init_files:
        assert init_file.exists(), f"__init__.py missing in {init_file.parent}"
        assert init_file.is_file(), f"{init_file} is not a file"
