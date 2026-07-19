"""
Integration tests for project setup tasks (T001b, T001c).

These tests verify that the directory structure is correctly created
and that .gitkeep files are properly initialized.
"""
import os
import pytest
import subprocess
import sys

# Required directories from T001b
REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/visualizations",
    "tests",
    "tests/unit",
    "tests/integration",
    "docs"
]

# Directories that should contain .gitkeep files (T001c)
GITKEEP_DIRS = REQUIRED_DIRS

def test_directories_exist():
    """Verify that all required directories exist after running setup_directories.py."""
    missing_dirs = []
    for dir_path in REQUIRED_DIRS:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        pytest.fail(f"The following directories are missing: {', '.join(missing_dirs)}")

def test_gitkeep_files_exist():
    """Verify that .gitkeep files exist in all specified directories."""
    missing_gitkeeps = []
    for dir_path in GITKEEP_DIRS:
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        if not os.path.isfile(gitkeep_path):
            missing_gitkeeps.append(dir_path)
    
    if missing_gitkeeps:
        pytest.fail(f"The following directories are missing .gitkeep files: {', '.join(missing_gitkeeps)}")

def test_gitkeep_content():
    """Verify that .gitkeep files contain expected content."""
    for dir_path in GITKEEP_DIRS:
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        if os.path.isfile(gitkeep_path):
            with open(gitkeep_path, 'r') as f:
                content = f.read()
                assert "# This file ensures the directory is tracked by Git" in content, \
                    f".gitkeep in {dir_path} has unexpected content"

def test_setup_directories_script_runs():
    """Verify that the setup_directories.py script runs without errors."""
    result = subprocess.run(
        [sys.executable, "code/setup_directories.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"setup_directories.py failed: {result.stderr}"

def test_setup_gitkeep_script_runs():
    """Verify that the setup_gitkeep.py script runs without errors."""
    result = subprocess.run(
        [sys.executable, "code/setup_gitkeep.py"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"setup_gitkeep.py failed: {result.stderr}"
