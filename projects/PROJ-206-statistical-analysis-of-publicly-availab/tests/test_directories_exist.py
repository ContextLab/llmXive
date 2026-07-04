"""
Basic sanity checks to ensure the required project directory structure exists.

These tests verify that the foundational directories (src, tests, data, state)
have been created at the repository root as per Phase 1 Setup tasks.
"""

import os
from pathlib import Path

import pytest

def test_project_root_exists():
    """Verify that the current working directory or project root is accessible."""
    # The test runner should be invoked from the project root
    assert os.path.isdir("."), "Project root directory must exist."

def test_src_directory_exists(project_root: Path):
    """Verify that the 'src' directory exists at the project root."""
    src_path = project_root / "src"
    assert src_path.exists(), f"Directory 'src' not found at {src_path}"
    assert src_path.is_dir(), f"'src' exists but is not a directory at {src_path}"

def tests_directory_exists(project_root: Path):
    """Verify that the 'tests' directory exists at the project root."""
    tests_path = project_root / "tests"
    assert tests_path.exists(), f"Directory 'tests' not found at {tests_path}"
    assert tests_path.is_dir(), f"'tests' exists but is not a directory at {tests_path}"

def test_data_directory_exists(project_root: Path):
    """Verify that the 'data' directory exists at the project root."""
    data_path = project_root / "data"
    assert data_path.exists(), f"Directory 'data' not found at {data_path}"
    assert data_path.is_dir(), f"'data' exists but is not a directory at {data_path}"

def test_state_directory_exists(project_root: Path):
    """Verify that the 'state' directory exists at the project root."""
    state_path = project_root / "state"
    assert state_path.exists(), f"Directory 'state' not found at {state_path}"
    assert state_path.is_dir(), f"'state' exists but is not a directory at {state_path}"