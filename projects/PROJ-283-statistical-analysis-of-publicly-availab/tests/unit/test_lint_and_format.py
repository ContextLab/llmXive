"""
Test that linting (ruff) and formatting (black) checks pass with exit code 0.
This serves as verification for task T003: configuring linting and formatting.
"""
import subprocess
import sys
from pathlib import Path

# Determine the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_command(command: list[str]) -> subprocess.CompletedProcess:
    """Run a command in the project root and return the CompletedProcess."""
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_ruff_check():
    """Run ruff check and assert it exits with code 0."""
    result = _run_command([sys.executable, "-m", "ruff", "check", "."])
    assert result.returncode == 0, (
        f"ruff check failed with exit code {result.returncode}\\n"
        f"stdout:\\n{result.stdout}\\n"
        f"stderr:\\n{result.stderr}"
    )


def test_black_check():
    """Run black in check mode and assert it exits with code 0."""
    result = _run_command([sys.executable, "-m", "black", "--check", "."])
    assert result.returncode == 0, (
        f"black --check failed with exit code {result.returncode}\\n"
        f"stdout:\\n{result.stdout}\\n"
        f"stderr:\\n{result.stderr}"
    )