"""
Tests to verify the project directory structure exists and is writable.
"""
import os
import pytest
from pathlib import Path


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def test_required_directories_exist():
    """Verify that all required project directories exist."""
    root = get_project_root()
    required_dirs = [
        "src",
        "tests",
        "contracts",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "reports",
        "specs",
    ]

    for dir_path in required_dirs:
        full_path = root / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Path is not a directory: {full_path}"


def test_structure_is_writable():
    """Verify that we can write to the project directories."""
    root = get_project_root()
    test_file = root / "data" / "logs" / ".write_test"

    try:
        test_file.touch()
        assert test_file.exists()
        test_file.unlink()  # Clean up
    except (OSError, PermissionError) as e:
        pytest.fail(f"Cannot write to project directory: {e}")
