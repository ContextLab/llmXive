"""
Unit tests to verify the project directory structure and initialization files.
"""
import pytest
from pathlib import Path

def test_tests_directory_exists(project_root):
    """Verify the tests directory exists."""
    tests_dir = project_root / "tests"
    assert tests_dir.exists(), "tests/ directory does not exist"
    assert tests_dir.is_dir(), "tests/ is not a directory"

def test_unit_subdirectory_exists(project_root):
    """Verify the tests/unit subdirectory exists."""
    unit_dir = project_root / "tests" / "unit"
    assert unit_dir.exists(), "tests/unit/ directory does not exist"
    assert unit_dir.is_dir(), "tests/unit/ is not a directory"

def test_integration_subdirectory_exists(project_root):
    """Verify the tests/integration subdirectory exists."""
    integration_dir = project_root / "tests" / "integration"
    assert integration_dir.exists(), "tests/integration/ directory does not exist"
    assert integration_dir.is_dir(), "tests/integration/ is not a directory"

def test_tests_init_file_exists(project_root):
    """Verify tests/__init__.py exists."""
    init_file = project_root / "tests" / "__init__.py"
    assert init_file.exists(), "tests/__init__.py does not exist"

def test_unit_init_file_exists(project_root):
    """Verify tests/unit/__init__.py exists."""
    init_file = project_root / "tests" / "unit" / "__init__.py"
    assert init_file.exists(), "tests/unit/__init__.py does not exist"

def test_integration_init_file_exists(project_root):
    """Verify tests/integration/__init__.py exists."""
    init_file = project_root / "tests" / "integration" / "__init__.py"
    assert init_file.exists(), "tests/integration/__init__.py does not exist"

def test_conftest_exists(project_root):
    """Verify tests/conftest.py exists."""
    conftest_file = project_root / "tests" / "conftest.py"
    assert conftest_file.exists(), "tests/conftest.py does not exist"
