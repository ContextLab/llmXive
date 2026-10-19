"""
Unit test for ``code/create_data_folders.py``.
The test imports the ``create_folders`` function, invokes it,
and asserts that the expected directories exist on disk.
"""

import os
from pathlib import Path

import pytest

# Import the function from the script we just created.
from code.create_data_folders import create_folders, paths

@pytest.fixture(scope="function")
def cleanup_directories():
    """
    Ensure a clean state before each test by removing the directories
    if they already exist. The test itself will recreate them.
    """
    dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("validation"),
        paths.results(""),
    ]
    # Remove directories if they exist (ignore errors)
    for d in dirs:
        if d.is_dir():
            # Remove all contents recursively
            for root, _, files in os.walk(d, topdown=False):
                for name in files:
                    os.remove(Path(root) / name)
            # Remove empty directory
            try:
                d.rmdir()
            except OSError:
                pass
    yield
    # Cleanup after test run
    for d in dirs:
        if d.is_dir():
            for root, _, files in os.walk(d, topdown=False):
                for name in files:
                    os.remove(Path(root) / name)
            try:
                d.rmdir()
            except OSError:
                pass

def test_create_folders_creates_all_directories(cleanup_directories):
    """
    Verify that ``create_folders`` creates the four required directories.
    """
    created = create_folders()
    expected_dirs = {
        paths.data("raw"),
        paths.data("processed"),
        paths.data("validation"),
        paths.results(""),
    }

    # All returned paths should be in the expected set
    assert set(created) == expected_dirs

    # Each expected directory must exist on disk after the call
    for d in expected_dirs:
        assert d.is_dir(), f"Directory {d} was not created"