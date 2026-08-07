"""
Integration test to verify the full project directory structure exists.
This test validates the outcome of T004.
"""
import os
from pathlib import Path
import pytest


def test_required_directories_exist():
    """
    Verify that all required directories from T004 exist in the project root.
    """
    # The test file is at tests/test_directory_structure.py
    # Project root is parent of tests/
    project_root = Path(__file__).resolve().parent.parent
    
    required_paths = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/reports",
        "docs"
    ]
    
    missing = []
    for rel_path in required_paths:
        full_path = project_root / rel_path
        if not full_path.exists():
            missing.append(rel_path)
        elif not full_path.is_dir():
            missing.append(rel_path + " (is not a directory)")
    
    if missing:
        pytest.fail(f"The following required directories are missing or invalid: {missing}")
    
    # If we get here, all directories exist
    assert True