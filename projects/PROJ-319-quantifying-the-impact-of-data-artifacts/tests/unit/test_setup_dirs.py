"""
Unit tests for the directory setup script logic.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the logic directly to test it without file system side effects in this scope
# We will mock the Path operations or run the function in a temp directory
from code.setup_dirs import create_directories, get_project_root

def test_create_directories_structure(tmp_path):
    """Test that create_directories creates the expected folder hierarchy."""
    expected_dirs = [
        "code",
        "code/synthetic",
        "code/metrics",
        "code/analysis",
        "code/io",
        "data/raw",
        "data/synthetic",
        "data/processed",
        "data/validation",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "logs"
    ]

    create_directories(tmp_path)

    for dir_name in expected_dirs:
        full_path = tmp_path / dir_name
        assert full_path.exists(), f"Directory {dir_name} was not created"
        assert full_path.is_dir(), f"Path {dir_name} exists but is not a directory"

def test_create_directories_idempotent(tmp_path):
    """Test that running create_directories twice does not fail."""
    create_directories(tmp_path)
    # Run again
    create_directories(tmp_path)
    
    # Verify all still exist
    assert (tmp_path / "code").exists()
    assert (tmp_path / "data/raw").exists()
    assert (tmp_path / "logs").exists()