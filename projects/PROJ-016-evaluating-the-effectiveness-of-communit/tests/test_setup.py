"""
Tests to verify the project structure creation.
"""
import os
import pytest

REQUIRED_DIRS = [
    "code/data",
    "code/analysis",
    "code/tests",
    "data/raw",
    "data/processed",
    "docs/output"
]

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_directory_exists(dir_path):
    """Verify that each required project directory exists."""
    assert os.path.isdir(dir_path), f"Required directory missing: {dir_path}"

def test_code_data_structure():
    """Verify specific sub-structure within code/data."""
    # Check that code/data exists and is a directory
    assert os.path.isdir("code/data")
    # Check that code/analysis exists
    assert os.path.isdir("code/analysis")
    # Check that code/tests exists
    assert os.path.isdir("code/tests")

def test_data_storage_structure():
    """Verify data storage directories exist."""
    assert os.path.isdir("data/raw")
    assert os.path.isdir("data/processed")

def test_docs_output_structure():
    """Verify documentation output directory exists."""
    assert os.path.isdir("docs/output")