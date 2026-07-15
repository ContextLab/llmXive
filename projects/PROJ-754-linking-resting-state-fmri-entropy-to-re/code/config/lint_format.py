"""
Configuration and execution utilities for linting (ruff) and formatting (black).

This module provides functions to check installation status and run
linting/formatting commands as subprocesses.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd: list[str], description: str, check: bool = True) -> bool:
    """
    Run a shell command and return True if successful.

    Args:
        cmd: Command and arguments as a list.
        description: Human-readable description for logging.
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        True if the command succeeded.
    """
    print(f"Running: {description}...")
    try:
        subprocess.run(cmd, check=check, text=True)
        print(f"✓ {description} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}.")
        if not check:
            return False
        raise


def check_ruff_installed() -> bool:
    """Check if ruff is installed and accessible."""
    try:
        subprocess.run(
            ["ruff", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_black_installed() -> bool:
    """Check if black is installed and accessible."""
    try:
        subprocess.run(
            ["black", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run_lint_check() -> bool:
    """Run ruff check on the project."""
    if not check_ruff_installed():
        print("Error: ruff is not installed. Please install it via `pip install ruff`.")
        return False
    return run_command(
        ["ruff", "check", "."],
        "Lint check (ruff)",
        check=False,  # Don't raise on lint errors, just report them
    )


def run_format_check() -> bool:
    """Run black check (diff mode) on the project."""
    if not check_black_installed():
        print("Error: black is not installed. Please install it via `pip install black`.")
        return False
    return run_command(
        ["black", "--check", "."],
        "Format check (black)",
        check=False,
    )


def run_lint_fix() -> bool:
    """Run ruff check with automatic fixes."""
    if not check_ruff_installed():
        print("Error: ruff is not installed. Please install it via `pip install ruff`.")
        return False
    return run_command(
        ["ruff", "check", ".", "--fix"],
        "Lint fix (ruff)",
    )


def run_format_fix() -> bool:
    """Run black formatter."""
    if not check_black_installed():
        print("Error: black is not installed. Please install it via `pip install black`.")
        return False
    return run_command(
        ["black", "."],
        "Format fix (black)",
    )


def main():
    """Entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Manage linting and formatting for the project."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run lint and format checks (fail if issues found).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run lint and format fixers (apply changes).",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Verify dependencies are installed (ruff, black).",
    )

    args = parser.parse_args()

    if args.install:
        ruff_ok = check_ruff_installed()
        black_ok = check_black_installed()
        if ruff_ok and black_ok:
            print("✓ All formatting tools installed.")
            sys.exit(0)
        else:
            print("✗ Missing tools. Run: pip install ruff black")
            sys.exit(1)

    if args.check:
        success = True
        if not run_lint_check():
            success = False
        if not run_format_check():
            success = False
        sys.exit(0 if success else 1)

    if args.fix:
        run_lint_fix()
        run_format_fix()
        sys.exit(0)

    # Default: help
    parser.print_help()


if __name__ == "__main__":
    main()