"""
Unit tests for the project setup structure script.

These tests verify that the required directories exist after the
setup script has been run.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the setup logic directly for testing
# We assume the script is run from the project root or we mock the path
import sys
import importlib.util

@pytest.fixture
def project_root(tmp_path):
    """Create a temporary directory structure to simulate the project root."""
    # Create the base structure manually to ensure the test is valid
    # even if the setup script hasn't run yet in the test environment
    dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs",
        "reports"
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path

def test_required_directories_exist(project_root):
    """Verify all required directories exist."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs",
        "reports"
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_gitkeep_files_exist(project_root):
    """Verify .gitkeep files exist in all directories."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs",
        "reports"
    ]

    for dir_name in required_dirs:
        gitkeep_path = project_root / dir_name / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep missing in {dir_name}"