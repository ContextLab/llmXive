"""
Test that the project's Black and Ruff configurations pass on an empty codebase.
This provides the verification required for task T002b.
"""

import subprocess
import sys
from pathlib import Path

def run_command(command: list[str]) -> None:
    """Run a command and raise an AssertionError if it fails."""
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command {' '.join(command)} failed with exit code {result.returncode}.\n"
            f"Output:\n{result.stdout}"
        )

def test_black_check() -> None:
    """Run `black --check` on the project root."""
    # Black expects a path; we give the project root (parent of this test file)
    project_root = Path(__file__).resolve().parent.parent
    run_command([sys.executable, "-m", "black", "--check", str(project_root)])

def test_ruff_check() -> None:
    """Run `ruff check` on the project root."""
    project_root = Path(__file__).resolve().parent.parent
    run_command([sys.executable, "-m", "ruff", "check", str(project_root)])