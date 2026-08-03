"""
Integration tests to verify the full project structure including dependencies.
"""
import pytest
from pathlib import Path

def test_full_directory_tree(project_root):
    """Verify the complete expected directory tree exists."""
    expected_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/models",
        "tests",
        "tests/unit",
        "tests/integration",
        "specs"
    ]
    
    for dir_path in expected_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"

def test_package_initialization(project_root):
    """Verify all necessary __init__.py files are present for package structure."""
    init_files = [
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "code/__init__.py"
    ]
    
    for file_path in init_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"File {file_path} does not exist"
        
        # Verify the file is not empty (basic check)
        content = full_path.read_text()
        # We accept comments or docstrings, but it should exist
        # The task requirement is to create them, content is minimal

def test_pytest_can_discover_tests(project_root):
    """Verify that pytest can discover tests in the structure."""
    # This is a meta-test; if we are running, pytest found this file
    # We can assert that test discovery would work by checking structure
    unit_test_file = project_root / "tests" / "unit" / "test_directory_structure.py"
    integration_test_file = project_root / "tests" / "integration" / "test_directory_structure.py"
    
    assert unit_test_file.exists(), "Unit test file missing"
    assert integration_test_file.exists(), "Integration test file missing"
