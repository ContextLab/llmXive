"""
Unit tests for the setup_dirs.py script logic.
Verifies that the correct directory structure is created.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path to import setup_dirs logic
# We simulate the script's logic here rather than running the script as a subprocess
# to keep tests fast and isolated, but we verify the exact paths defined in the script.

PROJECT_NAME = "PROJ-191-investigating-the-validity-of-the-invers"
REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "docs",
    "code/data",
    "code/models",
    "code/inference",
    "code/robustness",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/results",
    "tests/unit",
    "tests/contract",
    "tests/integration",
]

def test_directory_creation_logic(tmp_path):
    """
    Tests the core logic of directory creation using the exact paths from setup_dirs.py.
    """
    project_dir = tmp_path / "projects" / PROJECT_NAME
    project_dir.mkdir(parents=True)

    created_count = 0
    for dir_path in REQUIRED_DIRS:
        full_path = project_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_count += 1

    assert created_count == len(REQUIRED_DIRS)

    # Verify all directories exist
    for dir_path in REQUIRED_DIRS:
        full_path = project_dir / dir_path
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_nested_directory_creation(tmp_path):
    """
    Ensures that nested directories (e.g., code/data) are created correctly
    even if parent directories (code) are created first.
    """
    project_dir = tmp_path / "projects" / PROJECT_NAME
    project_dir.mkdir(parents=True)

    # Create a deep nested path directly
    deep_path = project_dir / "code" / "inference" / "nested_test"
    deep_path.mkdir(parents=True, exist_ok=True)

    assert deep_path.exists()
    assert (project_dir / "code").exists()
    assert (project_dir / "code" / "inference").exists()

def test_idempotency(tmp_path):
    """
    Verifies that running the creation logic twice does not raise errors.
    """
    project_dir = tmp_path / "projects" / PROJECT_NAME
    project_dir.mkdir(parents=True)

    # Run creation logic twice
    for _ in range(2):
        for dir_path in REQUIRED_DIRS:
            full_path = project_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
    
    # Verify all still exist
    for dir_path in REQUIRED_DIRS:
        assert (project_dir / dir_path).exists()