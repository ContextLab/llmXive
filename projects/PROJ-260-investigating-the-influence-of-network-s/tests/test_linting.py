"""
Test that the project passes linting and formatting checks.

The verification for task T004 requires that:
  * `ruff check .` reports no violations
  * `black --check .` reports no formatting issues
This test runs both tools and asserts a zero exit status.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("command", [
    ["ruff", "check", "."],
    ["black", "--check", "."],
])
def test_lint_and_format(command):
    """
    Execute the given command and ensure it exits with code 0.

    The commands are expected to be available in the environment
    (installed via the project's `requirements.txt`).
    """
    # Run the command in the project root
    result = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2],  # project root
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Debug output for CI logs
    print(f"Running {' '.join(command)}")
    print(result.stdout)

    assert result.returncode == 0, (
        f"Command {' '.join(command)} failed with exit code {result.returncode}.\n"
        f"Output:\n{result.stdout}"
    )
