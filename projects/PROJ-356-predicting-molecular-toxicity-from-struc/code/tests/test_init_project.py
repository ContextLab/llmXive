"""
Tests for the project initialization script.

These tests verify that the init_project.py script correctly creates
the required directory structure.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.init_project import create_directory_structure, verify_structure, REQUIRED_DIRS


class TestInitProject:
    """Test suite for project initialization functionality."""

    def test_create_directory_structure_creates_all_dirs(self, tmp_path):
        """Test that create_directory_structure creates all required directories."""
        # Create directories
        results = create_directory_structure(tmp_path, REQUIRED_DIRS)
        
        # Verify all directories were created
        assert len(results) == len(REQUIRED_DIRS)
        
        for full_path, was_created in results:
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} exists but is not a directory"

    def test_create_directory_structure_idempotent(self, tmp_path):
        """Test that running create_directory_structure twice doesn't cause errors."""
        # First run
        results1 = create_directory_structure(tmp_path, REQUIRED_DIRS)
        created_first = sum(1 for _, created in results1 if created)
        
        # Second run
        results2 = create_directory_structure(tmp_path, REQUIRED_DIRS)
        created_second = sum(1 for _, created in results2 if created)
        
        # Second run should create nothing new
        assert created_second == 0
        
        # All directories should still exist
        for full_path, _ in results2:
            assert full_path.exists()

    def test_verify_structure_returns_true_for_complete(self, tmp_path):
        """Test that verify_structure returns True when all dirs exist."""
        # Create all directories
        create_directory_structure(tmp_path, REQUIRED_DIRS)
        
        # Verify
        all_exist, missing = verify_structure(tmp_path, REQUIRED_DIRS)
        
        assert all_exist is True
        assert len(missing) == 0

    def test_verify_structure_returns_false_for_missing(self, tmp_path):
        """Test that verify_structure returns False when some dirs are missing."""
        # Create only some directories
        partial_dirs = REQUIRED_DIRS[:5]
        create_directory_structure(tmp_path, partial_dirs)
        
        # Verify with full list
        all_exist, missing = verify_structure(tmp_path, REQUIRED_DIRS)
        
        assert all_exist is False
        assert len(missing) > 0
        assert len(missing) == len(REQUIRED_DIRS) - len(partial_dirs)

    def test_required_dirs_are_non_empty(self):
        """Test that REQUIRED_DIRS is not empty and contains valid paths."""
        assert len(REQUIRED_DIRS) > 0
        
        for dir_path in REQUIRED_DIRS:
            assert isinstance(dir_path, str)
            assert len(dir_path) > 0
            assert not dir_path.startswith("/")  # Should be relative
            assert not dir_path.endswith("/")

    def test_directory_structure_contains_critical_paths(self):
        """Test that critical project directories are in REQUIRED_DIRS."""
        critical_dirs = [
            "code",
            "code/src",
            "code/tests",
            "data",
            "results",
            "models",
            "config",
            "docs",
            "contracts",
            "scripts",
        ]
        
        for critical_dir in critical_dirs:
            assert critical_dir in REQUIRED_DIRS, f"Critical directory {critical_dir} not found"

def test_init_project_creates_structure(tmp_path):
    """Integration test: run the main function and verify structure."""
    # Create a temporary project root
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Import and run main
    from scripts.init_project import main
    exit_code = main(project_root)
    
    assert exit_code == 0
    
    # Verify critical directories exist
    critical_dirs = [
        "code", "data", "results", "models", "config", "docs", "contracts", "scripts"
    ]
    
    for dir_name in critical_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Critical directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory"

def test_critical_directories_exist_in_project(tmp_path):
    """Test that the script creates all critical directories."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    from scripts.init_project import main
    exit_code = main(project_root)
    
    assert exit_code == 0
    
    # Check specific critical paths
    critical_paths = [
        "code/src",
        "code/src/features",
        "code/src/models",
        "code/tests/unit",
        "data/raw",
        "data/processed",
        "results/plots",
        "models",
    ]
    
    for path_str in critical_paths:
        full_path = project_root / path_str
        assert full_path.exists(), f"Critical path {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"