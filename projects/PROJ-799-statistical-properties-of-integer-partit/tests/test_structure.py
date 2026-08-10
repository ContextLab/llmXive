"""
Contract tests for T001a: Directory structure creation.
Verifies that all required directories and placeholder files exist.
"""
import os
import pytest
from pathlib import Path

# Determine project root (parent of 'tests')
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
PROJECT_SUBDIR = "projects/PROJ-799-statistical-properties-of-integer-partit"
PROJECT_PATH = PROJECT_ROOT / PROJECT_SUBDIR
STATE_PROJECTS_PATH = PROJECT_ROOT / "state" / "projects"

REQUIRED_DIRS = [
    "code",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/schemas",
    "tests",
    "tests/data",
    "docs"
]

REQUIRED_FILES = [
    (PROJECT_PATH, "README.md"),
    (PROJECT_PATH, ".gitignore"),
    (PROJECT_PATH, "requirements.txt"),
    (STATE_PROJECTS_PATH, "PROJ-799.yaml"),
]

def test_project_directory_exists():
    """Verify the main project directory exists."""
    assert PROJECT_PATH.exists(), f"Project directory not found: {PROJECT_PATH}"
    assert PROJECT_PATH.is_dir(), f"Project path is not a directory: {PROJECT_PATH}"

def test_state_projects_directory_exists():
    """Verify the state/projects directory exists at repository root."""
    assert STATE_PROJECTS_PATH.exists(), f"State projects directory not found: {STATE_PROJECTS_PATH}"
    assert STATE_PROJECTS_PATH.is_dir(), f"State projects path is not a directory: {STATE_PROJECTS_PATH}"

@pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
def test_required_subdirectory_exists(dir_path):
    """Verify each required subdirectory exists within the project."""
    full_path = PROJECT_PATH / dir_path
    assert full_path.exists(), f"Required directory missing: {full_path}"
    assert full_path.is_dir(), f"Required path is not a directory: {full_path}"

@pytest.mark.parametrize("dir_path, filename", REQUIRED_FILES)
def test_required_placeholder_file_exists(dir_path, filename):
    """Verify each required placeholder file exists."""
    full_path = dir_path / filename
    assert full_path.exists(), f"Required file missing: {full_path}"
    assert full_path.is_file(), f"Required path is not a file: {full_path}"

def test_project_structure_isolation():
    """Verify state/projects is NOT inside the project folder."""
    # Ensure state/projects is at repo root, not nested inside PROJ-799
    nested_path = PROJECT_PATH / "state" / "projects"
    assert not nested_path.exists(), "state/projects should not be inside the project folder"
