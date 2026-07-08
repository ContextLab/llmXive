"""
Linting and formatting configuration for the project.

This module centralizes configuration for flake8 and black to ensure
consistent code style across the project.
"""

import subprocess
import sys
from pathlib import Path


def run_flake8(path: str = "code", max_line_length: int = 88) -> int:
    """
    Run flake8 linting on the specified path.

    Args:
        path: Directory or file path to lint. Defaults to 'code'.
        max_line_length: Maximum line length allowed. Defaults to 88 (black compatible).

    Returns:
        Exit code from flake8 (0 if no issues, non-zero otherwise).
    """
    cmd = [
        sys.executable, "-m", "flake8",
        path,
        f"--max-line-length={max_line_length}",
        "--exclude=venv,env,build,dist,.git",
        "--ignore=E203,W503"  # Black compatibility
    ]
    result = subprocess.run(cmd)
    return result.returncode


def run_black(path: str = "code", check_only: bool = False) -> int:
    """
    Run black code formatter on the specified path.

    Args:
        path: Directory or file path to format. Defaults to 'code'.
        check_only: If True, only check formatting without modifying files.

    Returns:
        Exit code from black (0 if successful, non-zero otherwise).
    """
    cmd = [
        sys.executable, "-m", "black",
        path
    ]
    if check_only:
        cmd.append("--check")

    result = subprocess.run(cmd)
    return result.returncode


def run_isort(path: str = "code", check_only: bool = False) -> int:
    """
    Run isort import sorter on the specified path.

    Args:
        path: Directory or file path to sort. Defaults to 'code'.
        check_only: If True, only check sorting without modifying files.

    Returns:
        Exit code from isort (0 if successful, non-zero otherwise).
    """
    cmd = [
        sys.executable, "-m", "isort",
        path,
        "--profile=black",
        "--line-length=88"
    ]
    if check_only:
        cmd.append("--check-only")

    result = subprocess.run(cmd)
    return result.returncode


def main():
    """Main entry point for linting and formatting checks."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run linting and formatting tools on the codebase."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run in check-only mode (fail if issues found, don't modify)."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run in fix mode (attempt to automatically fix issues)."
    )
    parser.add_argument(
        "--path",
        default="code",
        help="Path to run checks on (default: code)."
    )

    args = parser.parse_args()

    if args.check or args.fix:
        check_only = args.check
    else:
        check_only = False

    print(f"Running linting and formatting checks on '{args.path}'...")

    # Run isort first to sort imports
    print("\n[1/3] Running isort...")
    isort_code = run_isort(args.path, check_only=check_only)

    # Run black to format code
    print("\n[2/3] Running black...")
    black_code = run_black(args.path, check_only=check_only)

    # Run flake8 for linting (black and isort may have fixed some issues)
    print("\n[3/3] Running flake8...")
    flake8_code = run_flake8(args.path)

    print("\n--- Summary ---")
    print(f"isort: {'PASSED' if isort_code == 0 else 'FAILED'}")
    print(f"black: {'PASSED' if black_code == 0 else 'FAILED'}")
    print(f"flake8: {'PASSED' if flake8_code == 0 else 'FAILED'}")

    if isort_code == 0 and black_code == 0 and flake8_code == 0:
        print("\nAll checks passed!")
        return 0
    else:
        print("\nSome checks failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
