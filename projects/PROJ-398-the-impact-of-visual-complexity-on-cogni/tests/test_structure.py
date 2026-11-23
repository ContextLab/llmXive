"""
Tests for the project’s directory‑creation utilities.

Two separate concerns are verified:

1. Data directories are created by ``setup_data_directories.main`` (existing test).
2. Code package directories are created by ``setup_code_directories.main`` (new test).

The existing test for data directories is retained, and a new test
``test_code_directories_exist`` is added to satisfy the T001a verification
requirement.
"""

import os
from pathlib import Path

import pytest

# Existing import – used by the original data‑directory test
from setup_data_directories import main as run_data_structure_creation

# New import – used for the code‑directory test
from setup_code_directories import main as run_code_structure_creation


def test_data_directories_exist():
    """
    Verify that the data directory hierarchy is created.
    """
    # Run the data‑directory creation script
    run_data_structure_creation()

    # Expected data directories (relative to project root)
    expected = [
        Path("data/stimuli"),
        Path("data/processed"),
        Path("data/measurements"),
        Path("data/raw"),
    ]

    missing = [str(p) for p in expected if not p.is_dir()]
    assert not missing, f"Missing data directories: {', '.join(missing)}"


def test_code_directories_exist():
    """
    Verify that the required code package directories are created.
    """
    # Run the code‑directory creation script
    run_code_structure_creation()

    # Expected code directories (relative to project root)
    expected = [
        Path("src/lib"),
        Path("src/metrics"),
        Path("src/experiment"),
        Path("src/analysis"),
        Path("tests"),
    ]

    missing = [str(p) for p in expected if not p.is_dir()]
    assert not missing, f"Missing code directories: {', '.join(missing)}"


# Ensure the test module can be imported directly by pytest without side effects.
# The ``if __name__ == '__main__'`` guard is unnecessary because pytest handles
# test discovery. This file solely defines the two tests above.