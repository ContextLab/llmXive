"""
tests/test_skeleton.py
-----------------------

Integration test that ensures the ``create_skeleton`` script creates the
required repository layout.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Import the function under test.
from create_skeleton import main as create_main


@pytest.fixture
def temporary_project(tmp_path: Path) -> Path:
    """
    Provide an isolated temporary directory that mimics the project root.
    The fixture changes the working directory to the temporary location,
    runs the skeleton creation, and yields the path for further checks.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Run the script – it will create the directories in ``tmp_path``.
        with pytest.raises(SystemExit) as excinfo:
            create_main()
        # The script exits with ``0`` on success.
        assert excinfo.value.code == 0
        yield tmp_path
    finally:
        os.chdir(original_cwd)


def test_directories_exist(temporary_project: Path) -> None:
    """
    Verify that each expected top‑level directory now exists.
    """
    expected = [
        "src",
        "tests",
        "data",
        "results",
        "docs",
        "contracts",
    ]
    for name in expected:
        assert (temporary_project / name).is_dir(), f"{name} directory missing"
