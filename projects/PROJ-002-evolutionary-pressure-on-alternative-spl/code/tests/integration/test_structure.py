"""
Integration test to verify the presence of all required test subdirectories.
"""
import os
import pytest
from pathlib import Path

def test_all_test_directories_present():
    """
    Verify that unit/, integration/, and contract/ directories exist
    relative to the tests root.
    """
    tests_root = Path(__file__).parent.parent
    required_dirs = ["unit", "integration", "contract"]
    
    for dir_name in required_dirs:
        dir_path = tests_root / dir_name
        assert dir_path.exists(), f"Required directory {dir_path} is missing"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_init_files_present():
    """
    Verify that __init__.py files exist in all test subdirectories
    to make them proper Python packages.
    """
    tests_root = Path(__file__).parent.parent
    required_dirs = ["unit", "integration", "contract"]
    
    for dir_name in required_dirs:
        init_file = tests_root / dir_name / "__init__.py"
        assert init_file.exists(), f"__init__.py missing in {dir_name}/"
