"""
Tests for directory structure creation.
Verifies that all required project directories exist.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code directory to path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    return code_dir

@pytest.fixture
def temp_base_path(tmp_path):
    """Create a temporary base path for testing directory creation."""
    return tmp_path

def test_tests_directory_exists(add_code_to_path):
    """Verify that the code/tests/ directory exists."""
    tests_dir = add_code_to_path / "tests"
    assert tests_dir.exists(), f"Directory {tests_dir} does not exist"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_all_directories_exist(add_code_to_path):
    """Verify all required project directories exist."""
    required_dirs = [
        "scripts",
        "data/raw",
        "data/processed",
        "data/splits",
        "models",
        "tests",
        "utils"
    ]
    
    for dir_path in required_dirs:
        full_path = add_code_to_path / dir_path
        assert full_path.exists(), f"Required directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"