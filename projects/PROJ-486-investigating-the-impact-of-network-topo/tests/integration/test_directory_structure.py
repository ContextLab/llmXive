"""
Integration test to verify the full directory structure exists
and contains necessary __init__.py files if expected.
"""
import os
import pytest

def test_required_directories_exist():
    """
    Check that the standard project directories exist in the root.
    """
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/visualizations",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    for d in required_dirs:
        assert os.path.isdir(d), f"Required directory {d} is missing"

def test_init_files_exist():
    """
    Verify that __init__.py files exist in code and tests.
    """
    assert os.path.isfile("code/__init__.py"), "code/__init__.py missing"
    assert os.path.isfile("tests/__init__.py"), "tests/__init__.py missing"
