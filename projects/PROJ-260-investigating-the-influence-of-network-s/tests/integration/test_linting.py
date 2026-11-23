"""
Integration test to verify that the codebase passes linting (ruff) and formatting (black)
with zero violations, as required by task T004.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root():
    """Return the absolute path to the project root (the directory containing this file's parent)."""
    return Path(__file__).resolve().parents[2]  # tests/integration/ -> project root


def run_command(command, cwd):
    """Run a shell command and raise if it exits with a non‑zero status."""
    result = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        print(f"Command failed: {' '.join(command)}", file=sys.stderr)
        print("Output:", result.stdout, file=sys.stderr)
        raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout)
    return result.stdout


def test_ruff_check(project_root):
    """Run `ruff check .` and assert it reports no violations."""
    # The `--quiet` flag suppresses the summary line; we only care about exit code.
    run_command(["ruff", "check", ".", "--quiet"], cwd=project_root)


def test_black_check(project_root):
    """Run `black --check .` and assert it reports no violations."""
    # Black exits with code 0 when no files would be reformatted.
    run_command(["black", "--check", "."], cwd=project_root)