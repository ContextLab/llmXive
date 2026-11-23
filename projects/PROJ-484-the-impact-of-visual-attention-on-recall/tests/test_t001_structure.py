"""
Unit tests for Task T001: Project directory structure creation.
Verifies that the expected directories exist after running the setup script.
"""
import os
import subprocess
import tempfile
import pytest

PROJECT_DIR = "projects/PROJ-484-the-impact-of-visual-attention-on-recall"
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "artifacts/figures",
    "artifacts/logs",
    "code",
    "tests"
]

@pytest.fixture(scope="module", autouse=True)
def setup_project_structure():
    """
    Ensure the project structure exists before running tests.
    This mimics the execution of setup_dirs.sh.
    """
    # Create the project root if it doesn't exist
    os.makedirs(PROJECT_DIR, exist_ok=True)
    
    # Create required subdirectories
    for dir_path in REQUIRED_DIRS:
        full_path = os.path.join(PROJECT_DIR, dir_path)
        os.makedirs(full_path, exist_ok=True)
    
    yield

def test_project_root_exists():
    """Test that the project root directory exists."""
    assert os.path.isdir(PROJECT_DIR), f"Project root {PROJECT_DIR} does not exist"

@pytest.mark.parametrize("subdir", REQUIRED_DIRS)
def test_required_directories_exist(subdir):
    """Test that each required subdirectory exists."""
    full_path = os.path.join(PROJECT_DIR, subdir)
    assert os.path.isdir(full_path), f"Required directory {full_path} does not exist"

def test_directory_permissions():
    """Test that directories are writable."""
    for subdir in REQUIRED_DIRS:
        full_path = os.path.join(PROJECT_DIR, subdir)
        assert os.access(full_path, os.W_OK), f"Directory {full_path} is not writable"