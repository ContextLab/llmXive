"""
Test that the project's linting (ruff) and formatting (black) configurations
are valid and pass without errors.

This test runs:
  - `ruff check .` to ensure the codebase conforms to the ruff linting rules.
  - `black --check .` to verify that the code is correctly formatted
    according to the project's Black configuration.

Both commands must exit with a return code of 0 for the test to pass.
"""
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root():
    """Return the absolute path to the project root directory."""
    return Path(__file__).resolve().parent.parent


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Execute a command via subprocess.run, capturing stdout and stderr."""
    return subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_ruff_check(project_root):
    """Run `ruff check .` and assert it exits cleanly."""
    result = run_command(["ruff", "check", "."], cwd=project_root)
    # Debug output in case of failure
    if result.returncode != 0:
        print("Ruff stdout:", result.stdout)
        print("Ruff stderr:", result.stderr)
    assert result.returncode == 0, "Ruff linting failed"


def test_black_check(project_root):
    """Run `black --check .` and assert it exits cleanly."""
    result = run_command(["black", "--check", "."], cwd=project_root)
    # Debug output in case of failure
    if result.returncode != 0:
        print("Black stdout:", result.stdout)
        print("Black stderr:", result.stderr)
    assert result.returncode == 0, "Black formatting check failed"