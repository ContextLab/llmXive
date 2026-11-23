"""Integration test that ensures the code base passes Ruff linting."""

import subprocess
import sys

def test_ruff_lint_passes():
    """Run ``ruff check code/`` and assert a zero exit status."""
    result = subprocess.run(
        ["ruff", "check", "code/"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, (
        f"Ruff reported linting errors:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )
