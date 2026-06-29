"""
Unit test for the ``code.cleanup`` module.

The test simply verifies that the ``run_black`` and ``run_flake8`` helper
functions can be imported and that they return an integer exit code when
invoked on a harmless target (the test file itself).  The actual formatting
and linting checks are performed by the external tools, which are already
declared as dependencies of the project.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Import the functions from the module we just added.
from code.cleanup import run_black, run_flake8


@pytest.mark.parametrize("tool_func", [run_black, run_flake8])
def test_tool_runs_on_self(tool_func):
    """
    Ensure that each tool can be executed on the current file without raising
    an exception and returns an integer exit code.
    """
    # Use this test file as the target; both tools accept a single file path.
    target = Path(__file__)

    rc = tool_func(target)

    # ``black`` returns 0 when the file is already formatted.
    # ``flake8`` returns 0 when there are no lint errors.
    # In either case the return code must be an integer.
    assert isinstance(rc, int)
    # Non‑zero exit codes are allowed (e.g., if the test file violates a rule)
    # but the function must not crash.
    # We simply assert that the call completed successfully.
    assert rc >= 0