"""
Unit test for task T001a: Verify project directory structure creation.
"""
import os
import pytest
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "artifacts",
    "artifacts/checkpoints",
    "artifacts/results"
]

def test_directory_structure_exists():
    """
    Verify that the main project directory and all required subdirectories exist.
    """
    # Ensure the script has been run (or run it here for the test)
    script_path = Path("code/create_project_structure.py")
    if script_path.exists():
        subprocess.run([sys.executable, str(script_path)], check=True)

    # Check main project directory
    assert PROJECT_ROOT.exists(), f"Project root {PROJECT_ROOT} does not exist"
    assert PROJECT_ROOT.is_dir(), f"{PROJECT_ROOT} is not a directory"

    # Check each required subdirectory
    for subdir in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / subdir
        assert full_path.exists(), f"Required subdirectory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_gitkeep_files_exist():
    """
    Verify that .gitkeep files were created to ensure directory tracking.
    """
    for subdir in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / subdir / ".gitkeep"
        assert full_path.exists(), f".gitkeep file missing in {PROJECT_ROOT / subdir}"