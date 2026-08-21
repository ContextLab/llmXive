import os
import pytest
from pathlib import Path

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def test_required_directories_exist():
    """Verify that the core project directories exist."""
    root = get_project_root()
    required_dirs = [
        root / "src",
        root / "tests",
        root / "contracts",
        root / "data",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "logs",
        root / "reports",
        root / "specs",
        root / "code",
    ]
    
    for directory in required_dirs:
        assert directory.exists(), f"Required directory missing: {directory}"
        assert directory.is_dir(), f"Path is not a directory: {directory}"

def test_structure_is_writable():
    """Verify that we can create temporary files in the data directories."""
    root = get_project_root()
    test_file = root / "data" / "logs" / ".write_test"
    try:
        test_file.touch()
        assert test_file.exists()
    finally:
        if test_file.exists():
            test_file.unlink()
