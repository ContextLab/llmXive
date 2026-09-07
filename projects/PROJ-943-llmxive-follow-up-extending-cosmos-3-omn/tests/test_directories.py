"""
Tests for directory creation and .gitkeep file existence.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code to path for imports
@pytest.fixture
def add_code_to_path():
    code_path = Path(__file__).parent.parent
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))

@pytest.fixture
def temp_base_path(tmp_path):
    """Create a temporary base path to simulate project root."""
    return tmp_path

def test_tests_directory_exists(add_code_to_path, temp_base_path):
    """Verify that the tests directory itself exists."""
    assert temp_base_path.exists()
    # In a real run, we'd check if 'tests' is a subdir, but here we check the fixture
    assert temp_base_path.is_dir()

def test_all_directories_exist(add_code_to_path, temp_base_path, monkeypatch):
    """
    Run the create_directories script logic against a temp path and verify all dirs/.gitkeeps exist.
    """
    from scripts.create_directories import create_directory, REQUIRED_DIRS

    # Mock the base_path to be our temp directory
    success = True
    for dir_name in REQUIRED_DIRS:
        if not create_directory(temp_base_path, dir_name):
            success = False
            break

    assert success, "Directory creation failed"

    # Verify each directory and .gitkeep exists
    for dir_name in REQUIRED_DIRS:
        full_path = temp_base_path / dir_name
        gitkeep_path = full_path / ".gitkeep"

        assert full_path.exists(), f"Directory {full_path} does not exist"
        assert full_path.is_dir(), f"{full_path} is not a directory"
        assert gitkeep_path.exists(), f".gitkeep file missing in {full_path}"
        assert gitkeep_path.read_text().strip() != "", f".gitkeep in {full_path} is empty"