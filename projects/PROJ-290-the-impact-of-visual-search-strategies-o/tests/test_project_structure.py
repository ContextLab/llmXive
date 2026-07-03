"""
Tests to verify the project directory structure created by T001a.
"""
import os
import pytest
from pathlib import Path

PROJECT_NAME = "PROJ-290-the-impact-of-visual-search-strategies-o"
BASE_PATH = Path("projects") / PROJECT_NAME

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "results/figures",
    "results/reports",
    "tests",
    "state"
]

@pytest.fixture(scope="module")
def project_root():
    return BASE_PATH

def test_project_base_directory_exists(project_root):
    """Assert that the main project directory exists."""
    assert project_root.exists(), f"Base project directory {project_root} does not exist."
    assert project_root.is_dir(), f"{project_root} is not a directory."

@pytest.mark.parametrize("subdir", REQUIRED_DIRS)
def test_required_subdirectories_exist(project_root, subdir):
    """Assert that each required subdirectory exists."""
    full_path = project_root / subdir
    assert full_path.exists(), f"Required directory {full_path} does not exist."
    assert full_path.is_dir(), f"{full_path} exists but is not a directory."

def test_nested_directories_exist(project_root):
    """Assert that nested directories like data/raw and results/figures exist."""
    nested_paths = [
        "data/raw",
        "data/processed",
        "results/figures",
        "results/reports"
    ]
    for subdir in nested_paths:
        full_path = project_root / subdir
        assert full_path.exists(), f"Nested directory {full_path} does not exist."
        assert full_path.is_dir(), f"{full_path} exists but is not a directory."