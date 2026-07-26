"""
CI test for T001d: Verify repository skeleton directories exist.

This test fails if any of the required skeleton directories are missing
from the project root. It ensures the project structure is intact before
proceeding with further development or CI steps.
"""
import os
import pytest
from pathlib import Path


REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    "results",
    "docs",
    "contracts",
]


@pytest.fixture
def project_root():
    """Return the project root directory (parent of the tests/ directory)."""
    return Path(__file__).resolve().parent.parent


def test_repository_skeleton_directories_exist(project_root):
    """
    CI step that fails if any skeleton directory is missing.
    
    Checks for the existence of:
    - src
    - tests
    - data
    - results
    - docs
    - contracts
    
    If any directory is missing, the test fails with a descriptive error.
    """
    missing_dirs = []
    for dir_name in REQUIRED_DIRS:
        dir_path = project_root / dir_name
        if not dir_path.is_dir():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        pytest.fail(
            f"Repository skeleton is incomplete. Missing directories: {', '.join(missing_dirs)}\n"
            f"Expected directories in project root: {REQUIRED_DIRS}"
        )