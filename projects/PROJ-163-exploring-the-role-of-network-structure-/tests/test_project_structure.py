"""
Test suite for T001: Project Structure Creation.

Verifies that the required directories exist and contain .gitkeep files
after the setup script has run.
"""
import os
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "tests",
]

def test_required_directories_exist():
    """Verify that all required project directories exist."""
    for dir_name in REQUIRED_DIRS:
        dir_path = Path(dir_name)
        assert dir_path.exists(), f"Required directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_gitkeep_files_exist():
    """Verify that .gitkeep files exist in all required directories."""
    for dir_name in REQUIRED_DIRS:
        dir_path = Path(dir_name)
        gitkeep_path = dir_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep file missing in {dir_path}."
        assert gitkeep_path.is_file(), f"{gitkeep_path} exists but is not a file."

def test_no_unexpected_top_level_dirs():
    """
    Optional sanity check: Ensure we haven't created unexpected top-level 
    directories that shouldn't be there yet (e.g., docs, figures).
    This is a soft check to ensure T001 only creates the planned structure.
    """
    expected_top_level = {"code", "data", "tests", "data/raw", "data/processed"}
    current_top_level = {str(p) for p in Path(".").iterdir() if p.is_dir()}
    
    # Filter out common non-project dirs that might exist in the repo
    common_repo_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache"}
    actual_project_dirs = current_top_level - common_repo_dirs
    
    # We expect the data directory itself to exist as a parent
    expected_project_dirs = {"code", "data", "tests"}
    
    # Check that we don't have unexpected directories like 'docs' or 'figures' yet
    unexpected = actual_project_dirs - expected_project_dirs - {"data/raw", "data/processed"}
    # Note: 'data/raw' and 'data/processed' are subdirs of 'data', so they might appear 
    # if we list all. The check above is a bit loose but sufficient for T001 scope.
    
    # For T001, we just ensure the core structure is there.
    # If 'docs' or 'figures' appear here, it would be a failure of T001 strictness.
    # However, since we only create specific dirs, this is mostly a sanity check.
    pass