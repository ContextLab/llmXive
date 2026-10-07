"""
Unit test to verify that the required project directories exist.
Implements verification for task T001a.
"""
import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """Assert that code/, data/raw/, data/processed/, data/results/, and tests/ exist."""
    # Determine project root (assuming tests are in tests/ dir)
    root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "tests",
    ]

    for dir_path in required_dirs:
        assert dir_path.exists(), f"Required directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_directories_are_writable():
    """Assert that we can create a temporary file in each required directory."""
    root = Path(__file__).resolve().parent.parent
    
    test_dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "tests",
    ]

    for dir_path in test_dirs:
        temp_file = dir_path / ".test_write_permission"
        try:
            temp_file.touch()
            temp_file.unlink()
        except OSError as e:
            pytest.fail(f"Directory {dir_path} is not writable: {e}")