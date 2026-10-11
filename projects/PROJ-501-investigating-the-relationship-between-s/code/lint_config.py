"""
Linting and formatting configuration runner.

Provides CLI entry points to run Black, Flake8, and Pylint on the project's
codebase. The configuration files for each tool are placed at the project
root (see .flake8, .pylintrc, pyproject.toml).
"""

import subprocess
import sys
from pathlib import Path


def _run_tool(command: list[str], description: str) -> None:
    """Run a subprocess command and exit on failure."""
    print(f"Running {description}...")
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{description} failed with exit code {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        sys.exit(result.returncode)
    else:
        print(f"{description} completed successfully.")
        print(result.stdout)


def run_black() -> None:
    """Run Black formatter on the code directory."""
    _run_tool(
        ["black", str(Path(__file__).parent.parent / "code")],
        "Black formatter",
    )


def run_flake8() -> None:
    """Run Flake8 linter on the code directory."""
    _run_tool(
        ["flake8", str(Path(__file__).parent.parent / "code")],
        "Flake8 linter",
    )


def run_pylint() -> None:
    """Run Pylint on the code directory."""
    _run_tool(
        ["pylint", str(Path(__file__).parent.parent / "code")],
        "Pylint linter",
    )


def main() -> None:
    """Execute all linting and formatting tools."""
    run_black()
    run_flake8()
    run_pylint()


if __name__ == "__main__":
    main()
