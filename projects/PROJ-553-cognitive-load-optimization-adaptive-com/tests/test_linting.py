"""
Linting & formatting verification tests.

These tests ensure that the project conforms to the Black formatter
and Ruff linter configurations defined in ``pyproject.toml`` and
``.ruff.toml``.  They are executed by ``pytest -q`` as part of the
verification step for task T003.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_command(command: list[str]) -> subprocess.CompletedProcess:
    """Run a command in the project root and capture its output."""
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_black_check():
    """Assert that ``black --check .`` reports no formatting violations."""
    result = _run_command([sys.executable, "-m", "black", "--check", "."])
    assert (
        result.returncode == 0
    ), f"Black formatting violations detected:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"


def test_ruff_check():
    """Assert that ``ruff check .`` reports no linting violations."""
    result = _run_command([sys.executable, "-m", "ruff", "check", "."])
    assert (
        result.returncode == 0
    ), f"Ruff linting violations detected:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"