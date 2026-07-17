"""
Tests for T001: Project Directory Structure Setup.

This module verifies that the project directory structure is correctly created.
"""
import os
import pytest
from pathlib import Path

def test_project_directories_exist():
    """
    Test that the required project directories exist.
    
    This test verifies the existence of:
    - projects/PROJ-068-evaluating-the-performance-of-different-/code/
    - projects/PROJ-068-evaluating-the-performance-of-different-/tests/
    - projects/PROJ-068-evaluating-the-performance-of-different-/data/
    - projects/PROJ-068-evaluating-the-performance-of-different-/results/
    """
    project_name = "PROJ-068-evaluating-the-performance-of-different-"
    base_path = Path("projects") / project_name
    
    required_dirs = [
        "code",
        "tests",
        "data",
        "results",
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory does not exist: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_directories_are_writable():
    """
    Test that the created directories are writable.
    """
    project_name = "PROJ-068-evaluating-the-performance-of-different-"
    base_path = Path("projects") / project_name
    
    test_file_name = ".write_test"
    
    try:
        # Try writing a test file to each directory
        for dir_name in ["code", "tests", "data", "results"]:
            dir_path = base_path / dir_name
            test_file = dir_path / test_file_name
            test_file.touch()
            assert test_file.exists()
            test_file.unlink()  # Clean up
    except Exception as e:
        pytest.fail(f"Failed to write to directory: {e}")