"""
Utility module to manage linting and formatting configurations.
This module ensures that ruff and black are configured correctly
and provides helper functions to run them programmatically if needed.
"""

import subprocess
import sys
from pathlib import Path


def run_linter(check_only: bool = True) -> int:
    """
    Run ruff linter on the code directory.

    Args:
        check_only: If True, only check for errors (exit non-zero if found).
                   If False, attempt to fix issues.

    Returns:
        Exit code of the ruff process.
    """
    cmd = ["ruff", "check", "code/"]
    if not check_only:
        cmd.append("--fix")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: ruff not found. Please install it via pip.", file=sys.stderr)
        return 1


def run_formatter(check_only: bool = True) -> int:
    """
    Run black formatter on the code directory.

    Args:
        check_only: If True, only check for formatting issues (exit non-zero if found).
                   If False, attempt to fix formatting.

    Returns:
        Exit code of the black process.
    """
    cmd = ["black", "code/"]
    if check_only:
        cmd.append("--check")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please install it via pip.", file=sys.stderr)
        return 1


def main():
    """
    Main entry point for running linter and formatter checks.
    Exits with code 0 if all checks pass, 1 otherwise.
    """
    print("Running linter (ruff)...")
    lint_exit = run_linter(check_only=True)

    print("Running formatter check (black)...")
    fmt_exit = run_formatter(check_only=True)

    if lint_exit == 0 and fmt_exit == 0:
        print("All linting and formatting checks passed.")
        sys.exit(0)
    else:
        if lint_exit != 0:
            print("Linter failed. Run 'ruff check --fix code/' to attempt fixes.")
        if fmt_exit != 0:
            print("Formatter check failed. Run 'black code/' to format code.")
        sys.exit(1)


if __name__ == "__main__":
    main()