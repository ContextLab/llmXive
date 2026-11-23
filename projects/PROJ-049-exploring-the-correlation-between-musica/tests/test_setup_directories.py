"""
tests/test_setup_directories.py

Simple test that the ``create_directory_structure`` function creates all required
directories and that they exist after the call.
"""

import os
from pathlib import Path

import pytest

# Import the function from the module under test
from setup_directories import create_directory_structure

@pytest.mark.parametrize(
    "dirs",
    [
        None,  # default directories
    ],
)
def test_create_directory_structure(tmp_path: Path, dirs):
    """
    Verify that ``create_directory_structure`` creates the expected directories.
    The test runs in an isolated temporary directory to avoid side‑effects on the
    repository's real structure.
    """
    # Change working directory to the temporary path so that the function resolves
    # the project root relative to this location.
    original_cwd = Path.cwd()
    os.chdir(tmp_path)

    try:
        # Call the function – it should create the directories under the temp root
        create_directory_structure(dirs)

        # Determine the expected paths (relative to the temporary root)
        expected = [
            tmp_path / "data" / "raw",
            tmp_path / "data" / "processed",
            tmp_path / "code",
            tmp_path / "tests",
            tmp_path / "results",
            tmp_path / "logs",
        ]

        # Assert each expected directory exists and is indeed a directory
        for p in expected:
            assert p.is_dir(), f"Expected directory {p} does not exist"
    finally:
        # Restore original working directory regardless of test outcome
        os.chdir(original_cwd)