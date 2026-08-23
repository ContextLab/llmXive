"""
Test to verify the project structure was created correctly.
Verifies that code/, data/, docs/, and tests/ directories exist.
"""
import os
import pytest
from pathlib import Path

def test_project_root_exists():
    """Test that the project root is accessible."""
    assert Path(".").exists()

def test_code_directory_exists():
    """Test that the code/ directory exists."""
    code_dir = Path("code")
    assert code_dir.exists(), "Directory 'code/' does not exist"
    assert code_dir.is_dir(), "'code/' is not a directory"

def test_data_directory_exists():
    """Test that the data/ directory exists."""
    data_dir = Path("data")
    assert data_dir.exists(), "Directory 'data/' does not exist"
    assert data_dir.is_dir(), "'data/' is not a directory"

def test_docs_directory_exists():
    """Test that the docs/ directory exists."""
    docs_dir = Path("docs")
    assert docs_dir.exists(), "Directory 'docs/' does not exist"
    assert docs_dir.is_dir(), "'docs/' is not a directory"

def test_tests_directory_exists():
    """Test that the tests/ directory exists."""
    tests_dir = Path("tests")
    assert tests_dir.exists(), "Directory 'tests/' does not exist"
    assert tests_dir.is_dir(), "'tests/' is not a directory"

def test_directory_structure_is_complete():
    """Test that all required top-level directories exist."""
    required_dirs = ["code", "data", "docs", "tests"]
    missing = [d for d in required_dirs if not Path(d).exists()]
    assert not missing, f"Missing directories: {missing}"
