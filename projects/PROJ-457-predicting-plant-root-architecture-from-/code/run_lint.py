"""Run Black and Flake8 linting using the project‑specific configuration files.

This script is part of task **T003** and ensures that the codebase
conforms to the formatting and style rules defined in ``pyproject.toml``
(for Black) and the Flake8 configuration embedded in the same file.
It formats the code with Black (in check‑only mode) and runs Flake8.
The script exits with code 0 only when both tools report no issues.
"""

import subprocess
import sys
from pathlib import Path


def _run_command(command: list[str]) -> None:
    """Execute a command, streaming stdout/stderr and exiting on failure."""
    proc = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(
            f"Command {' '.join(command)} failed with exit code {proc.returncode}\\n"
        )
        sys.exit(proc.returncode)


def main() -> None:
    # Resolve the project root (two levels up from this file)
    project_root = Path(__file__).resolve().parent.parent

    # Black: run in check‑only mode so it only verifies formatting
    black_config = project_root / "pyproject.toml"
    _run_command(
        [
            "black",
            "--config",
            str(black_config),
            "--check",
            str(project_root),
        ]
    )

    # Flake8: it reads its configuration from the same pyproject.toml
    flake8_config = project_root / "pyproject.toml"
    _run_command(
        [
            "flake8",
            "--config",
            str(flake8_config),
            str(project_root),
        ]
    )


if __name__ == "__main__":
    main()
