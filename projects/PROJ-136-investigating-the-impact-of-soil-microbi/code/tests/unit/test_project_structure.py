"""
Unit tests for T001 project structure verification.

Tests that all required directories are created correctly.
"""

import os
import pytest
from pathlib import Path

# Expected directories relative to project root
EXPECTED_DIRS = [
    "data/raw",
    "data/processed",
    "code/analysis",
    "code/tests",
    "code/tests/contract",
    "code/tests/integration",
    "code/tests/unit",
    "state"
]

def get_project_root():
    """Get the project root directory (parent of code/)."""
    return Path(__file__).resolve().parent.parent.parent

@pytest.fixture
def root_path():
    return get_project_root()

@pytest.mark.parametrize("dir_path", EXPECTED_DIRS)
def test_directory_exists(root_path, dir_path):
    """Test that each required directory exists."""
    full_path = root_path / dir_path
    assert full_path.exists(), f"Directory does not exist: {full_path}"
    assert full_path.is_dir(), f"Path is not a directory: {full_path}"

def test_all_directories_exist(root_path):
    """Test that all required directories exist simultaneously."""
    missing = []
    for dir_path in EXPECTED_DIRS:
        full_path = root_path / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    assert len(missing) == 0, f"Missing directories: {missing}"

def test_nested_structure(root_path):
    """Test that nested directory structures are correct."""
    # Test specific nested paths
    nested_paths = [
        "data/raw",
        "data/processed",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit"
    ]
    
    for dir_path in nested_paths:
        full_path = root_path / dir_path
        assert full_path.exists(), f"Nested directory missing: {full_path}"
        # Verify parent directories exist
        assert full_path.parent.exists(), f"Parent directory missing: {full_path.parent}"