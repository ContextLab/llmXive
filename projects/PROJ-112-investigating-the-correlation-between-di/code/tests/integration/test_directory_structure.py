"""
Integration test to verify the project directory structure exists.
"""
import pytest
from pathlib import Path

def test_required_directories_exist(project_root, data_dir, processed_dir, results_dir):
    """Verify that all required directories exist."""
    required_dirs = [
        project_root,
        data_dir,
        processed_dir,
        results_dir,
        project_root / "src",
        project_root / "tests",
        project_root / "docs",
        project_root / "state",
    ]
    for d in required_dirs:
        assert d.exists(), f"Directory {d} does not exist"
        assert d.is_dir(), f"{d} exists but is not a directory"

def test_test_directories_exist(project_root):
    """Verify that test subdirectories exist."""
    test_dirs = [
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
    ]
    for d in test_dirs:
        assert d.exists(), f"Test directory {d} does not exist"
        assert d.is_dir(), f"{d} exists but is not a directory"
