"""
Unit test to verify that the required directory structure exists.
This test ensures T001a has been successfully executed.
"""
import os
import pytest
import sys

# Determine project root relative to this test file
# test file is at code/tests/unit/test_directory_structure.py
# project root is code/../
test_file_dir = os.path.dirname(os.path.abspath(__file__))
unit_dir = os.path.dirname(test_file_dir)
tests_dir = os.path.dirname(unit_dir)
code_dir = os.path.dirname(tests_dir)
project_root = os.path.dirname(code_dir)

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
    "state"
]

def test_project_directories_exist():
    """Assert that all required directories defined in T001a exist."""
    missing_dirs = []
    for rel_dir in REQUIRED_DIRS:
        full_path = os.path.join(project_root, rel_dir)
        if not os.path.isdir(full_path):
            missing_dirs.append(rel_dir)

    assert len(missing_dirs) == 0, (
        f"The following required directories are missing: {missing_dirs}. "
        "Please run scripts/setup_directories.py to initialize the project structure."
    )

def test_project_root_is_valid():
    """Assert that we can identify the project root correctly."""
    assert os.path.exists(os.path.join(project_root, "code"))
    assert os.path.exists(os.path.join(project_root, "data"))