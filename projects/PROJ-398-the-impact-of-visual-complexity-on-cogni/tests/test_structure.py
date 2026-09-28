"""
tests/test_structure.py
-----------------------

Unit tests that verify the existence of the required project directory
hierarchy. ``run_structure_creation`` invokes the creation scripts for
both the source code layout (``create_code_structure``) and the data
layout (``setup_data_directories``). The individual tests then assert that
the expected directories are present on disk.

The tests rely on the standard ``pytest`` framework and the ``Path``
class from ``pathlib``.
"""

import sys
from pathlib import Path

import pytest

# Import the creation scripts. They are expected to live in the ``code/``
# package and expose a ``main`` function.
from create_code_structure import main as create_code_main
from setup_data_directories import main as create_data_main

def run_structure_creation() -> None:
    """
    Execute the directory‑creation entry points for both code and data
    structures. This helper is used by the individual test cases.
    """
    # Ensure the current working directory is the project root.
    # The tests are executed from the repository root, so ``Path.cwd()``
    # already points there. If this ever changes, adjust accordingly.
    create_code_main()
    create_data_main()

def test_code_directories_exist() -> None:
    """
    Verify that the source‑code directories required by the project are
    present after ``run_structure_creation``.
    """
    run_structure_creation()
    project_root = Path.cwd()
    expected_dirs = [
        project_root / "src" / "lib",
        project_root / "src" / "metrics",
        project_root / "src" / "experiment",
        project_root / "src" / "analysis",
        project_root / "tests",
    ]
    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} does not exist."

def test_data_directories_exist() -> None:
    """
    Verify that the data directories required by the project are present
    after ``run_structure_creation``.
    """
    run_structure_creation()
    project_root = Path.cwd()
    expected_data_dirs = [
        project_root / "data" / "stimuli",
        project_root / "data" / "processed",
        project_root / "data" / "measurements",
        project_root / "data" / "raw",
    ]
    for d in expected_data_dirs:
        assert d.is_dir(), f"Expected data directory {d} does not exist."