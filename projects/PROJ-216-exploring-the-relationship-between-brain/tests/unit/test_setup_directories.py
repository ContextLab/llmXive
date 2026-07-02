"""
Unit tests for the directory setup functionality.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.setup_directories import create_directories, create_init_files

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_create_directories_creates_expected_paths(temp_project_root):
    """Test that create_directories creates the standard paths."""
    expected_paths = [
        "data/raw",
        "data/interim",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "reports",
    ]

    result = create_directories()

    # Verify all directories exist
    for path in expected_paths:
        assert os.path.isdir(path), f"Directory {path} was not created"

    # Verify return count (should be equal to number of paths since none existed)
    assert result == len(expected_paths)

def test_create_init_files(temp_project_root):
    """Test that create_init_files creates __init__.py files."""
    # First create the directories
    create_directories()
    
    # Now create init files
    create_init_files()

    expected_init_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]

    for init_file in expected_init_files:
        assert os.path.isfile(init_file), f"Init file {init_file} was not created"

def test_create_directories_idempotent(temp_project_root):
    """Test that running create_directories multiple times doesn't fail."""
    # Run twice
    result1 = create_directories()
    result2 = create_directories()

    # First run should create all, second run should create none
    expected_total = 7
    assert result1 == expected_total
    assert result2 == 0

def test_create_init_files_idempotent(temp_project_root):
    """Test that running create_init_files multiple times doesn't fail."""
    create_directories()
    
    result1 = create_init_files()
    result2 = create_init_files()
    
    # Both should complete without error (return type is None, but no exception)
    assert True