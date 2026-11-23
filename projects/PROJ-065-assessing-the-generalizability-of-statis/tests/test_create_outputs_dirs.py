"""
Basic test to verify that the ``create_outputs_dirs`` script creates the
expected directories. The test runs the script (importing its ``main``
function) and then checks that the directories exist on the filesystem.
"""

import os
from pathlib import Path

import pytest

# Import the script's main function.
from code.create_outputs_dirs import main as create_dirs_main


@pytest.fixture(scope="function")
def clean_output_dirs(tmp_path_factory):
    """
    Ensure a clean ``outputs`` hierarchy for each test run.
    The fixture creates a temporary project root and patches
    ``llmxive_toolkit.paths.root`` to point there.
    """
    # Create a temporary directory to act as the project root.
    temp_root = tmp_path_factory.mktemp("project_root")

    # Patch the toolkit's root path.
    from llmxive_toolkit import paths
    original_root = paths.root
    paths.root = str(temp_root)

    yield temp_root

    # Restore original root after test.
    paths.root = original_root
    # Cleanup is automatic with the temporary directory.


def test_create_output_directories(clean_output_dirs):
    """
    Run the directory‑creation script and assert that the three required
    directories exist.
    """
    # Execute the script's main function.
    create_dirs_main()

    # Expected directories relative to the temporary root.
    expected_dirs = [
        clean_output_dirs / "outputs",
        clean_output_dirs / "outputs" / "figures",
        clean_output_dirs / "outputs" / "reports",
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} to exist"

# The test can be run with ``pytest -q``; no explicit execution request is
# needed because pytest will discover this file automatically.