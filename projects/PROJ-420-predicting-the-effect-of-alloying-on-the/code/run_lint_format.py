"""Run Ruff and Black linting/formatting checks.

This script verifies that the project's codebase conforms to the
configured linting (ruff) and formatting (black) rules defined in
``code/pyproject.toml``. It exits with a non‑zero status if any
violations are detected, satisfying the verification requirement for
task T003.
"""

import subprocess
import sys
from pathlib import Path

def _run_tool(command: list[str]) -> None:
    """Execute a command and abort on failure.

    Parameters
    ----------
    command : list[str]
        The command and its arguments to execute.
    """
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"{command[0]} failed with the following output:\n{result.stdout}",
            file=sys.stderr,
        )
        sys.exit(result.returncode)
    else:
        print(f"{command[0]} passed without issues.")

def main() -> None:
    # Determine the project root (the directory containing the top‑level pyproject.toml)
    project_root = Path(__file__).resolve().parents[1]

    # Ruff linting (uses the configuration in code/pyproject.toml)
    _run_tool(["ruff", str(project_root)])

    # Black formatting check (does not modify files)
    _run_tool(["black", "--check", str(project_root)])

if __name__ == "__main__":
    main()