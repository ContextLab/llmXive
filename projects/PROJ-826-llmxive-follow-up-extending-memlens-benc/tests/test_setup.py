"""
Test suite to verify the project directory structure is correctly created.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def base_path():
    """Return the project root path."""
    return Path(__file__).parent.parent

def test_data_raw_exists(base_path):
    """Test that data/raw directory exists."""
    assert (base_path / "data/raw").exists(), "data/raw directory is missing"
    assert (base_path / "data/raw").is_dir(), "data/raw is not a directory"

def test_data_processed_exists(base_path):
    """Test that data/processed directory exists."""
    assert (base_path / "data/processed").exists(), "data/processed directory is missing"
    assert (base_path / "data/processed").is_dir(), "data/processed is not a directory"

def test_code_exists(base_path):
    """Test that code directory exists."""
    assert (base_path / "code").exists(), "code directory is missing"
    assert (base_path / "code").is_dir(), "code is not a directory"

def test_tests_unit_exists(base_path):
    """Test that tests/unit directory exists."""
    assert (base_path / "tests/unit").exists(), "tests/unit directory is missing"
    assert (base_path / "tests/unit").is_dir(), "tests/unit is not a directory"

def test_state_projects_exists(base_path):
    """Test that state/projects directory exists."""
    assert (base_path / "state/projects").exists(), "state/projects directory is missing"
    assert (base_path / "state/projects").is_dir(), "state/projects is not a directory"

def test_placeholder_files_exist(base_path):
    """Test that required placeholder files exist."""
    required_files = [
        "code/__init__.py",
        "tests/__init__.py",
        "README.md",
        "requirements.txt"
    ]
    for file_path in required_files:
        full_path = base_path / file_path
        assert full_path.exists(), f"Required file missing: {file_path}"
        assert full_path.is_file(), f"{file_path} is not a file"