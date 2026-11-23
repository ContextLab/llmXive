import pytest
import os
import tempfile
from pathlib import Path
from code.setup_directories import create_project_structure, ensure_directory

def test_create_project_structure():
    """
    Test that create_project_structure creates the required directories:
    data/raw, data/processed, code, tests, results
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "test_proj"
        create_project_structure(root)

        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "tests",
            "results"
        ]

        for dir_name in required_dirs:
            full_path = root / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_ensure_directory_exists():
    """Test ensure_directory on an existing path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "existing_dir"
        path.mkdir()
        ensure_directory(path)
        assert path.exists()

def test_ensure_directory_creates():
    """Test ensure_directory creates a new path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "new_dir"
        assert not path.exists()
        ensure_directory(path)
        assert path.exists()
