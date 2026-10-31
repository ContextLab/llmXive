"""
Integration test that verifies the project's linting and formatting configuration.

The test runs the following commands:
  - ruff --config code/.ruff.toml .
  - black --check code/

Both commands must exit with status code 0, indicating that there are no linting
or formatting violations according to the repository's configuration.
"""

import subprocess
import sys
import pathlib

import pytest


@pytest.fixture(scope="module")
def project_root():
    """Return the absolute path to the repository root (the directory containing this file's grand‑parent)."""
    return pathlib.Path(__file__).resolve().parents[2]


def run_command(command, cwd):
    """Run a command via subprocess and return its CompletedProcess."""
    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return result


def test_ruff_lints_successfully(project_root):
    """Ruff must finish with exit code 0."""
    command = [sys.executable, "-m", "ruff", "--config", "code/.ruff.toml", "."]
    result = run_command(command, cwd=project_root)
    assert result.returncode == 0, f"Ruff failed with output:\\n{result.stdout}"


def test_black_formats_successfully(project_root):
    """Black must finish with exit code 0."""
    command = [sys.executable, "-m", "black", "--check", "code/"]
    result = run_command(command, cwd=project_root)
    assert result.returncode == 0, f"Black failed with output:\\n{result.stdout}"