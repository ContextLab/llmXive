"""
Unit tests for Task T001a: Directory Structure Creation.

These tests verify that the required project directories and files
are created correctly by the setup_directories.py script.
"""
import os
import sys
import pytest
from pathlib import Path
import shutil
import tempfile

# Add the project root to the path
repo_root = Path.cwd()
project_root = repo_root / "projects" / "PROJ-967-llmxive-follow-up-extending-beyond-scala"

def test_directories_exist():
    """Test that all required directories exist after setup."""
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests"
    ]
    
    for dir_path in required_dirs:
        assert dir_path.exists(), f"Directory does not exist: {dir_path}"
        assert dir_path.is_dir(), f"Not a directory: {dir_path}"

def test_package_init_files_exist():
    """Test that __init__.py files exist for code and tests packages."""
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "tests" / "__init__.py"
    ]
    
    for init_file in init_files:
        assert init_file.exists(), f"Package init file missing: {init_file}"
        assert init_file.is_file(), f"Not a file: {init_file}"

def test_gitkeep_files_exist():
    """Test that .gitkeep files exist in data directories."""
    gitkeep_files = [
        project_root / "data" / "raw" / ".gitkeep",
        project_root / "data" / "processed" / ".gitkeep",
        project_root / "results" / ".gitkeep"
    ]
    
    for gitkeep in gitkeep_files:
        assert gitkeep.exists(), f".gitkeep file missing: {gitkeep}"
        assert gitkeep.is_file(), f"Not a file: {gitkeep}"

def test_directory_permissions():
    """Test that directories have proper write permissions."""
    test_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "code",
        project_root / "tests"
    ]
    
    for dir_path in test_dirs:
        # Try to create a temporary file
        test_file = dir_path / "test_permission_check.tmp"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Directory {dir_path} is not writable: {e}")