"""
Unit tests to verify the project directory structure exists as required.
"""
import os
import pytest
import sys
from pathlib import Path

# Determine project root (parent of code/tests)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

REQUIRED_DIRS = [
    "src/models",
    "src/data",
    "src/training",
    "src/experiments",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "scripts",
    "data/results",
    "data/logs",
    "data/configs",
    "state",
]

def test_project_directories_exist():
    """Verify all required directories exist in the project root."""
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing.append(dir_path)
        elif not full_path.is_dir():
            missing.append(f"{dir_path} (is not a directory)")
    
    assert not missing, f"Missing required directories: {missing}"

def test_state_directory_contains_template():
    """Verify the state directory contains the required template file."""
    state_dir = PROJECT_ROOT / "state"
    template_file = state_dir / "project_state.yaml"
    
    assert state_dir.exists(), "state directory does not exist"
    assert template_file.exists(), f"State template file {template_file} does not exist"
    
    # Verify content has required keys
    content = template_file.read_text()
    assert "hashes" in content, "State template missing 'hashes' key"
    assert "artifacts" in content, "State template missing 'artifacts' key"
    assert "updated_at" in content, "State template missing 'updated_at' key"

def test_project_root_is_valid():
    """Verify the project root is correctly identified."""
    assert PROJECT_ROOT.exists(), "Project root path does not exist"
    # Check for typical markers of a Python project
    assert (PROJECT_ROOT / "pyproject.toml").exists() or (PROJECT_ROOT / "setup.py").exists(), \
        "Project root does not contain pyproject.toml or setup.py"
