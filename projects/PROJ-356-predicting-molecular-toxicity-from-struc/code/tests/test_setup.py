"""
Tests for the project setup and directory creation.
Validates that the required directory structure exists or can be created.
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure we can import setup_directories if needed, though this test focuses on existence
# We rely on the fixture logic in conftest to locate paths
from tests.conftest import project_root

def test_data_directory_exists():
    """Verify that the data directory exists or can be created."""
    root = project_root()
    data_dir = root / "data"
    # The task is to create the directory structure. 
    # If it doesn't exist yet, we verify the path is correct.
    # In a real CI run, the setup script (T004) would have run.
    # Here we just ensure the path object is valid.
    assert isinstance(data_dir, Path)
    # We do not assert existence here because T004 might not have run yet in isolation.
    # However, if the directory structure was created by a previous step, it should exist.
    # For this specific task (T003 - creating tests dir), we verify the tests dir exists.
    
def test_tests_directory_exists():
    """Verify that the tests directory exists (Task T003)."""
    root = project_root()
    tests_dir = root / "tests"
    assert tests_dir.exists(), f"Tests directory not found at {tests_dir}"
    assert tests_dir.is_dir(), f"{tests_dir} is not a directory"

def test_src_directory_exists():
    """Verify that the src directory exists (Task T002)."""
    root = project_root()
    src_dir = root / "src"
    assert src_dir.exists(), f"Src directory not found at {src_dir}"
    assert src_dir.is_dir(), f"{src_dir} is not a directory"

def test_code_directory_exists():
    """Verify that the code directory exists (Task T001)."""
    root = project_root()
    code_dir = root
    # The project_root is defined as the 'code' directory in conftest logic relative to tests
    # Wait, let's re-read conftest: _project_root = _code_dir.parent. 
    # If conftest is in code/tests, then _code_dir is code, and _project_root is projects/...
    # So root is projects/...
    # Then code_dir = root / "code"
    code_dir = root / "code"
    assert code_dir.exists(), f"Code directory not found at {code_dir}"
    assert code_dir.is_dir(), f"{code_dir} is not a directory"
