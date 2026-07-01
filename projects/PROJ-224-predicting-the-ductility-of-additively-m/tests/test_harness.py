"""
Basic test harness to verify the testing infrastructure is correctly configured.

This module provides a sanity check that pytest can discover and run tests
within the project structure.
"""
import sys
from pathlib import Path

def test_project_root_accessible():
    """Verify that the project root and key directories are accessible."""
    project_root = Path(__file__).parent.parent
    assert project_root.exists(), "Project root does not exist"
    
    required_dirs = ["code", "data", "tests", "specs"]
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Required directory '{dir_name}' not found at {dir_path}"

def test_pytest_discovery():
    """Verify that pytest can discover this test file."""
    # This is a meta-test to ensure the harness is working
    assert True, "Test harness is functional"

def test_imports_valid():
    """Verify that standard imports work without side effects."""
    try:
        import pandas
        import numpy
        import pytest
    except ImportError as e:
        pytest.fail(f"Required dependency missing: {e}")