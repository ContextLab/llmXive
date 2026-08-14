"""
Contract test for T004: Verify data directory .gitkeep files.

This test ensures that the data directory structure contains the
required .gitkeep placeholder files to ensure Git tracks the directories.
"""
import os
import sys
from pathlib import Path
import pytest

# Determine the project root
# Test file: projects/.../code/tests/data/test_t004_gitkeep.py
# Project root: projects/.../
TEST_FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = TEST_FILE_PATH.parent.parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

REQUIRED_DIRS = ["raw", "processed", "results"]

@pytest.fixture
def data_paths():
    """Returns a list of Path objects for the required data directories."""
    return [DATA_ROOT / d for d in REQUIRED_DIRS]

def test_data_directories_exist(data_paths):
    """Assert that the data subdirectories exist."""
    for path in data_paths:
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

def test_gitkeep_files_exist(data_paths):
    """Assert that .gitkeep files exist in each data subdirectory."""
    for path in data_paths:
        gitkeep_path = path / ".gitkeep"
        assert gitkeep_path.exists(), f"Missing .gitkeep file in {path}"
        assert gitkeep_path.is_file(), f"{gitkeep_path} is not a file"

def test_gitkeep_files_are_empty_or_valid(data_paths):
    """Assert that .gitkeep files are valid (empty or containing only whitespace)."""
    for path in data_paths:
        gitkeep_path = path / ".gitkeep"
        try:
            content = gitkeep_path.read_text()
            # .gitkeep files are typically empty, but whitespace is acceptable
            assert content.strip() == "", f"Content in {gitkeep_path} is not empty: '{content}'"
        except Exception as e:
            pytest.fail(f"Failed to read {gitkeep_path}: {e}")

def test_full_path_structure():
    """
    Verify the full path structure matches the task requirement:
    projects/PROJ-582-socratic-transformers-dialogue-based-sel/data/{raw,processed,results}/.gitkeep
    """
    # Construct expected paths relative to project root
    for dir_name in REQUIRED_DIRS:
        expected_path = DATA_ROOT / dir_name / ".gitkeep"
        assert expected_path.exists(), f"Expected path {expected_path} does not exist"