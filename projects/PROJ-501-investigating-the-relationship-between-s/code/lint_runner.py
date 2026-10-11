"""
Helper utilities to run shell commands for linting/formatting.

Provides a thin wrapper around subprocess calls to standardize output
handling for the linting configuration script.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a command and report its status.

    Parameters
    ----------
    cmd : list[str]
        Command and arguments to execute.
    description : str
        Human‑readable description of the command.

    Returns
    -------
    bool
        True if the command succeeded (exit code 0), False otherwise.
    """
    print(f"Executing: {description}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"{description} succeeded.")
        print(result.stdout)
        return True
    else:
        print(f"{description} failed with exit code {result.returncode}")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        return False


def main() -> None:
    """
    Example entry point that could be used to invoke the linting
    configuration script. Not used directly in the pipeline but kept
    for completeness.
    """
    from lint_config import main as lint_main

    lint_main()


if __name__ == "__main__":
    sys.exit(main())