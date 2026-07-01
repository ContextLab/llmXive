import os
import pytest
from pathlib import Path

# Determine project root relative to this test file
# tests/ is at root level, so root is parent of tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRECTORIES = [
    "data",
    "artifacts",
    "tests",
    "code/data",
    "code/models",
    "code/analysis",
]

@pytest.fixture(scope="module")
def project_root():
    return PROJECT_ROOT

@pytest.mark.parametrize("dir_name", REQUIRED_DIRECTORIES)
def test_directory_exists(project_root, dir_name):
    """
    Test that required directories exist in the project structure.
    This validates the outcome of T002 and T003.
    """
    dir_path = project_root / dir_name
    assert dir_path.exists(), f"Directory {dir_path} does not exist."
    assert dir_path.is_dir(), f"Path {dir_path} exists but is not a directory."

def test_code_directory_structure(project_root):
    """
    Specific test for the code/ subdirectory structure required by the pipeline.
    """
    code_dir = project_root / "code"
    assert code_dir.exists(), "Root 'code' directory missing."
    
    # Verify subdirectories are present
    subdirs = ["data", "models", "analysis"]
    for subdir in subdirs:
        subdir_path = code_dir / subdir
        assert subdir_path.exists(), f"Subdirectory code/{subdir} is missing."
        assert subdir_path.is_dir(), f"code/{subdir} is not a directory."