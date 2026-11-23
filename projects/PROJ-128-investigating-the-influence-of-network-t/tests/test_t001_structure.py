"""
Test for Task T001: Verify project directory structure.

This test ensures that all required directories exist and contain .gitkeep files.
"""
import os
from pathlib import Path
import pytest


REQUIRED_DIRS = [
    "code",
    "code/analysis",
    "code/preprocess",
    "code/reports",
    "code/utils",
    "data",
    "data/raw",
    "data/processed",
    "data/logs",
    "data/figures",
    "contracts",
    "tests",
    "tests/unit",
    "tests/integration",
    "docs",
    "figures",
]


def test_required_directories_exist():
    """Verify all required directories exist."""
    base_path = Path(".")
    
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"


def test_gitkeep_files_exist():
    """Verify .gitkeep files exist in all directories."""
    base_path = Path(".")
    
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        gitkeep_path = full_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep file missing in {dir_path}"