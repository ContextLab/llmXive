"""
tests/ci/test_skeleton_ci.py
----------------------------

CI‑style test that runs the ``check_skeleton`` module to confirm the
repository skeleton is present.  The test creates a temporary project
structure, invokes ``create_skeleton`` to build the layout, and then
runs ``check_skeleton.main`` which should exit with status 0.
"""

import os
import sys
from pathlib import Path

import pytest

from create_skeleton import main as create_main
from check_skeleton import main as check_main


@pytest.fixture
def temporary_project(tmp_path: Path) -> Path:
    """
    Set up an isolated temporary directory, run the skeleton creation script,
    and keep the directory as the current working directory for the CI check.
    """
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Build the skeleton.
        with pytest.raises(SystemExit) as excinfo:
            create_main()
        assert excinfo.value.code == 0
        yield tmp_path
    finally:
        os.chdir(original_cwd)


def test_skeleton_ci_passes(temporary_project: Path) -> None:
    """
    ``check_skeleton.main`` should succeed (exit code 0) when the skeleton
    exists.
    """
    with pytest.raises(SystemExit) as excinfo:
        check_main()
    assert excinfo.value.code == 0
