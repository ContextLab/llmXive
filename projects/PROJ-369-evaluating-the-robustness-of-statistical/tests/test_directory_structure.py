"""
Tests to verify the project directory structure exists as required.

These tests ensure that the foundational directory structure is in place
for the project to function correctly.
"""
import pytest
from pathlib import Path
import os
from src.utils.config import get_path


def test_required_directories_exist():
    """Test that all required top-level directories exist."""
    project_root = get_path("")
    
    required_dirs = [
        "src",
        "tests",
        "data",
        "results",
        "specs"
    ]
    
    for dir_name in required_dirs:
        dir_path = Path(project_root) / dir_name
        assert dir_path.exists(), f"Required directory does not exist: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_directory_setup_script_exists():
    """Test that the directory setup script exists."""
    project_root = get_path("")
    setup_script = Path(project_root) / "code" / "setup_directories.py"
    
    assert setup_script.exists(), f"Setup script not found: {setup_script}"

def test_tests_directory_is_importable():
    """Test that the tests directory is properly structured as a Python package."""
    tests_dir = get_path("tests")
    init_file = Path(tests_dir) / "__init__.py"
    
    assert init_file.exists(), f"tests/__init__.py does not exist"
    
    # Verify conftest.py exists for pytest configuration
    conftest = Path(tests_dir) / "conftest.py"
    assert conftest.exists(), f"tests/conftest.py does not exist"

def test_unit_test_directory_exists():
    """Test that the unit tests directory exists."""
    unit_dir = get_path("tests/unit")
    assert unit_dir.exists(), f"Unit tests directory does not exist: {unit_dir}"

def test_integration_test_directory_exists():
    """Test that the integration tests directory exists."""
    integration_dir = get_path("tests/integration")
    assert integration_dir.exists(), f"Integration tests directory does not exist: {integration_dir}"
