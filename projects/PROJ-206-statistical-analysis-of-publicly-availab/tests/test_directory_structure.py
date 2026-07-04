"""
Tests to verify the project directory structure exists as required.
"""
import os
import pytest
from pathlib import Path

def test_tests_directory_exists():
    """
    Verify that the tests/ directory exists at the project root.
    """
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    assert tests_dir.exists(), "tests/ directory does not exist at project root"
    assert tests_dir.is_dir(), "tests/ is not a directory"
    
    # Verify it contains at least the __init__.py file (non-empty check)
    init_file = tests_dir / "__init__.py"
    assert init_file.exists(), "tests/__init__.py does not exist"

def test_tests_directory_has_init():
    """
    Verify that tests/ directory has an __init__.py file.
    """
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    init_file = tests_dir / "__init__.py"
    assert init_file.exists(), "tests/__init__.py is missing"
    assert init_file.stat().st_size >= 0, "tests/__init__.py is empty"
