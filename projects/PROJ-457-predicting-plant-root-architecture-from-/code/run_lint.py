"""Run Black and Flake8 linting using the project‑specific configuration files.

This script is part of task **T003a–T003c** and ensures that the codebase
conforms to the formatting and style rules defined in ``code/pyproject.toml``
and ``code/.flake8``.
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
        sys.stderr.write(f"Command {' '.join(command)} failed with exit code {proc.returncode}\\n")
        sys.exit(proc.returncode)

def main() -> None:
    project_root = Path(__file__).resolve().parent.parent  # project root directory
    # Black: use the config file located in ``code/pyproject.toml``.
    black_config = project_root / "code" / "pyproject.toml"
    _run_command(["black", "--config", str(black_config), "--check", str(project_root)])

    # Flake8: point explicitly at the config file in ``code/.flake8``.
    flake8_config = project_root / "code" / ".flake8"
    _run_command(["flake8", "--config", str(flake8_config), str(project_root)])

if __name__ == "__main__":
    main()
