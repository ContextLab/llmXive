"""
Linting and Formatting Utility for PROJ-525.

This module provides command-line interfaces to run Ruff and Black
to ensure code quality and consistency across the project.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """
    Execute a shell command and report the result.

    Args:
        cmd: List of command arguments.
        description: Human-readable description of the action.

    Returns:
        True if the command succeeded, False otherwise.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )
        print(f"SUCCESS: {description} completed.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"ERROR: Command not found. Ensure {' '.join(cmd[:2])} is installed.")
        return False


def main() -> int:
    """
    Main entry point for linting and formatting.

    Usage:
        python code/lint_format.py check   # Run linter and formatter in check mode
        python code/lint_format.py fix     # Auto-fix issues where possible

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if len(sys.argv) < 2:
        print("Usage: python code/lint_format.py [check|fix]")
        print("  check: Run linters/formatters in non-modifying mode.")
        print("  fix:   Auto-fix linting errors and format code.")
        return 1

    mode = sys.argv[1].lower()
    project_root = Path(__file__).parent.parent

    # Change to project root to ensure config files are found
    os.chdir(project_root)

    success = True

    # 1. Run Black
    black_cmd = ["black", "--check"] if mode == "check" else ["black", "."]
    if mode == "fix":
        # Black fixes in place, no --check flag
        black_cmd = ["black", "."]

    if not run_command(black_cmd, "Black Formatting"):
        success = False

    # 2. Run Ruff
    ruff_cmd = ["ruff", "check"] if mode == "check" else ["ruff", "check", "--fix"]
    if mode == "fix":
        ruff_cmd = ["ruff", "check", "--fix"]

    if not run_command(ruff_cmd, "Ruff Linting"):
        success = False

    if success:
        print("All linting and formatting checks passed.")
        return 0
    else:
        print("Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())