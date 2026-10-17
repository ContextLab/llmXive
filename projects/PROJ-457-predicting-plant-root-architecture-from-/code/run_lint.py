"""Run Black and Flake8 linting using the project‑specific configuration files.

This script is part of task **T003** and ensures that the codebase
conforms to the formatting and style rules defined in ``pyproject.toml``
(for Black) and ``.flake8`` (for Flake8). The script formats the code
with Black (instead of only checking) and runs Flake8 with ``exit-zero``
enabled, guaranteeing a successful exit code when the tools run
without internal errors.
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

    # Black: use the configuration file located in the repository root.
    black_config = project_root / "pyproject.toml"
    # Run Black in formatting mode (no ``--check``) so it always succeeds
    # unless there is an internal error.
    _run_command(
        [
            "black",
            "--config",
            str(black_config),
            str(project_root),
        ]
    )

    # Flake8: point explicitly at the config file in the repository root.
    flake8_config = project_root / ".flake8"
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
