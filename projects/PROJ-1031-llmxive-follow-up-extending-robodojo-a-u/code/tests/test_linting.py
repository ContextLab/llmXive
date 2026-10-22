"""
Test that the project's linting and formatting configuration passes.

This test runs the ruff and black commands with the project's configuration
files and asserts that they exit with a zero status code, indicating no
linting errors and that the code is properly formatted.
"""
import subprocess
import sys
from pathlib import Path

import pytest

# Resolve the project root (the directory containing this test file's parent)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

@pytest.mark.parametrize(
    "command, cwd, expected_returncode",
    [
        (["ruff", "--config", str(PROJECT_ROOT / "code" / ".ruff.toml"), "."], PROJECT_ROOT, 0),
        (["black", "--check", str(PROJECT_ROOT / "code")], PROJECT_ROOT, 0),
    ],
)
def test_linting_and_formatting(command, cwd, expected_returncode):
    """Run the given command and ensure it exits successfully."""
    # Use the same Python interpreter's environment to ensure the tools are found
    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Print output for debugging in case of failure
    print(f"Command: {' '.join(command)}\nReturn code: {result.returncode}\nOutput:\n{result.stdout}")
    assert result.returncode == expected_returncode, (
        f"Command {' '.join(command)} failed with return code {result.returncode}. "
        f"Output:\n{result.stdout}"
    )