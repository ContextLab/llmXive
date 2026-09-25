"""
Integration tests for directory structure validation.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.setup_data_structure import setup_directories, get_project_root

@pytest.fixture
def temp_root():
    """Create a temporary directory to act as a temporary project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_required_directories_exist(temp_root):
    """
    Integration test: Ensure all required directories are created
    when setup_directories is run on a fresh root.
    """
    setup_directories(temp_root)

    required_dirs = [
        "src",
        "src/ingestion",
        "src/preprocessing",
        "src/analysis",
        "src/utils",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "docs",
        "state",
    ]

    for dir_name in required_dirs:
        dir_path = temp_root / dir_name
        assert dir_path.exists(), f"Required directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"

def test_test_directories_exist(temp_root):
    """
    Integration test: Ensure test directory structure is created.
    """
    setup_directories(temp_root)

    test_dirs = [
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]

    for dir_name in test_dirs:
        dir_path = temp_root / dir_name
        assert dir_path.exists(), f"Test directory missing: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"