"""
Linting and Formatting Configuration for PROJ-363.

This module provides helper functions to validate project code against
the configured Ruff (linting) and Black (formatting) standards.
It is designed to be run as a script or imported into CI pipelines.

Usage:
    python code/linting_config.py check
    python code/linting_config.py fix
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a shell command and return True if successful.

    Args:
        cmd: List of command arguments.
        description: Human-readable description of the action.

    Returns:
        True if the command exits with code 0, False otherwise.
    """
    print(f"Running: {description}...")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: Command not found. Please ensure {' '.join(cmd[:2])} is installed.")
        return False


def check_linting() -> bool:
    """Run Ruff to check for linting errors."""
    # Using ruff check instead of the deprecated 'ruff'
    cmd = [sys.executable, "-m", "ruff", "check", "code/", "tests/", "."]
    return run_command(cmd, "Linting check (Ruff)")


def check_formatting() -> bool:
    """Run Black to check for formatting issues."""
    cmd = [sys.executable, "-m", "black", "--check", "code/", "tests/"]
    return run_command(cmd, "Formatting check (Black)")


def fix_linting() -> bool:
    """Run Ruff to automatically fix linting errors."""
    # Using ruff check --fix
    cmd = [sys.executable, "-m", "ruff", "check", "--fix", "code/", "tests/", "."]
    return run_command(cmd, "Linting fix (Ruff)")


def fix_formatting() -> bool:
    """Run Black to automatically format code."""
    cmd = [sys.executable, "-m", "black", "code/", "tests/"]
    return run_command(cmd, "Formatting fix (Black)")


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python code/linting_config.py [check|fix]")
        sys.exit(1)

    action = sys.argv[1].lower()
    success = True

    if action == "check":
        print("Checking code quality and formatting...")
        if not check_linting():
            success = False
        if not check_formatting():
            success = False
    elif action == "fix":
        print("Fixing code quality and formatting...")
        if not fix_linting():
            success = False
        if not fix_formatting():
            success = False
    else:
        print(f"Unknown action: {action}. Use 'check' or 'fix'.")
        sys.exit(1)

    if success:
        print("\nAll checks passed or fixes applied successfully.")
        sys.exit(0)
    else:
        print("\nSome checks failed or fixes could not be applied.")
        sys.exit(1)


if __name__ == "__main__":
    main()
