"""
Test that the repository skeleton directories exist.

This test serves as a CI step: if any of the required top‑level
directories (src, tests, data, results, docs, contracts) are missing,
the test will fail, causing the CI job to fail.
"""

import pathlib

import pytest

# Determine the repository root assuming this file lives in
# <repo_root>/code/tests/
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# List of required top‑level directories for the skeleton
REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    "results",
    "docs",
    "contracts",
]


@pytest.mark.parametrize("directory", REQUIRED_DIRS)
def test_skeleton_directory_exists(directory: str):
    """
    Assert that each required skeleton directory exists at the repository root.
    """
    dir_path = REPO_ROOT / directory
    assert dir_path.is_dir(), f"Required skeleton directory missing: {dir_path}"