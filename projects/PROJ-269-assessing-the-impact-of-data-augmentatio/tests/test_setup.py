"""
Test suite to verify the project directory structure creation.
"""
import os
import pytest
from pathlib import Path

def test_directories_exist():
    """Verify that required project directories exist."""
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/derived",
        "results",
        "contracts"
    ]
    
    base_path = Path.cwd()
    
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        assert full_path.exists(), f"Directory {full_path} does not exist."
        assert full_path.is_dir(), f"{full_path} is not a directory."

def test_init_files_exist():
    """Verify that __init__.py files exist in code and tests."""
    base_path = Path.cwd()
    
    code_init = base_path / "code" / "__init__.py"
    tests_init = base_path / "tests" / "__init__.py"
    
    assert code_init.exists(), f"{code_init} does not exist."
    assert tests_init.exists(), f"{tests_init} does not exist."