"""
Tests for the directory setup script.
Verifies that the required directory structure exists after running setup_dirs.py.
"""
import os
import pytest
from pathlib import Path
import subprocess
import sys

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

@pytest.fixture
def setup_script(project_root):
    """Path to the setup script."""
    return project_root / "code" / "setup_dirs.py"

def test_setup_script_runs_successfully(setup_script, project_root):
    """Test that setup_dirs.py executes without errors."""
    result = subprocess.run(
        [sys.executable, str(setup_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Script failed with output: {result.stdout} {result.stderr}"

def test_required_directories_exist(project_root):
    """Test that all required directories exist after setup."""
    # Ensure setup has run first (in a real CI this would be a separate step)
    # For testing purposes, we run it here or assume it ran.
    # In a real scenario, we'd run the setup script in a separate test or fixture.
    
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests",
        "artifacts",
        "figures"
    ]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"Directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."

def test_data_subdirectories_exist(project_root):
    """Test that specific data subdirectories exist."""
    subdirs = ["raw", "processed", "logs"]
    for subdir in subdirs:
        dir_path = project_root / "data" / subdir
        assert dir_path.exists(), f"Directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} is not a directory."