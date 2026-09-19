import pytest
from pathlib import Path

def test_required_directories_exist(project_root):
    """Verify that the core project directories exist."""
    required_dirs = [
        "code/src",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "docs",
        "state",
    ]
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Required directory missing: {full_path}"
        assert full_path.is_dir(), f"Required path is not a directory: {full_path}"

def test_test_directories_exist(project_root):
    """Verify that the test sub-directories exist."""
    required_test_dirs = [
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
    ]
    for dir_path in required_test_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Required test directory missing: {full_path}"
        assert full_path.is_dir(), f"Required path is not a directory: {full_path}"
