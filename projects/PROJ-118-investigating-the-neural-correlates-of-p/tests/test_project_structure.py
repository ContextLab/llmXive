"""
Test suite for T001: Verify project structure creation.

This test ensures that the required directories exist and contain .gitkeep files.
"""
import os
import pytest

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "results"
]

@pytest.fixture
def project_root():
    """Return the current working directory as the project root."""
    return os.getcwd()

def test_required_directories_exist(project_root):
    """Assert that all required directories exist."""
    for dir_name in REQUIRED_DIRS:
        full_path = os.path.join(project_root, dir_name)
        assert os.path.isdir(full_path), f"Directory missing: {full_path}"

def test_gitkeep_files_exist(project_root):
    """Assert that .gitkeep files exist in all required directories."""
    for dir_name in REQUIRED_DIRS:
        full_path = os.path.join(project_root, dir_name)
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        assert os.path.isfile(gitkeep_path), f".gitkeep missing in: {full_path}"
