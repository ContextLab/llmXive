"""
Unit test for create_t001_root.py

The test ensures that invoking the ``main`` function creates the required
empty directory at:
    projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
"""

import shutil
from pathlib import Path

import pytest

# Import the script's main function
from create_t001_root import main as create_root_main

@pytest.fixture
def clean_target_dir():
    """
    Ensure the target directory does not exist before the test runs,
    and clean it up afterwards.
    """
    target = Path(
        "projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code"
    ).resolve()
    # Remove if it exists from a previous run
    if target.exists():
        shutil.rmtree(target)
    yield target
    # Cleanup after test
    if target.exists():
        shutil.rmtree(target)

def test_create_empty_directory(clean_target_dir):
    target = clean_target_dir

    # Pre‑condition: directory should not exist
    assert not target.exists()

    # Run the script
    create_root_main()

    # Post‑condition: directory exists and is empty
    assert target.is_dir()
    # ``list`` forces evaluation; should be empty
    assert list(target.iterdir()) == []