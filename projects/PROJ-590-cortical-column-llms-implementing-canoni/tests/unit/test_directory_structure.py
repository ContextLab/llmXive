import os
import pytest
import sys

# Define the required directories as per plan.md and T001a
REQUIRED_DIRS = [
    "src/models",
    "src/data",
    "src/training",
    "src/experiments",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "scripts",
    "data/results",
    "data/logs",
    "data/configs",
    "state",
]

def test_project_directories_exist():
    """
    Verifies that all required directories from T001a exist on the filesystem.
    This test fails if any directory is missing, ensuring the directory tree
    was actually created.
    """
    missing = []
    for d in REQUIRED_DIRS:
        if not os.path.isdir(d):
            missing.append(d)

    if missing:
        pytest.fail(f"Missing required directories: {missing}")

def test_project_root_is_valid():
    """
    Basic sanity check that the project root is not empty and contains
    the expected top-level structure (src, tests, etc.).
    """
    assert os.path.isdir("src"), "Project root must contain 'src' directory"
    assert os.path.isdir("tests"), "Project root must contain 'tests' directory"
    assert os.path.isdir("scripts"), "Project root must contain 'scripts' directory"
    assert os.path.isdir("data"), "Project root must contain 'data' directory"
    assert os.path.isdir("state"), "Project root must contain 'state' directory"
