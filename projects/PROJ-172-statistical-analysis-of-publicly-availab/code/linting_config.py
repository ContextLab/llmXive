"""
Configuration and execution helpers for linting (ruff) and formatting (black).
This module provides functions to run checks and fixes programmatically.
"""
import subprocess
import sys
import os
from pathlib import Path


def get_project_root() -> Path:
    """Return the project root directory (parent of the 'code' directory)."""
    current_file = Path(__file__).resolve()
    # Assuming this file is at code/linting_config.py
    return current_file.parent.parent


def run_ruff_check() -> int:
    """Run ruff check on the project. Returns exit code."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: ruff not found. Please install it via `pip install ruff`.", file=sys.stderr)
        return 1


def run_ruff_fix() -> int:
    """Run ruff check with --fix on the project. Returns exit code."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: ruff not found. Please install it via `pip install ruff`.", file=sys.stderr)
        return 1


def run_black_check() -> int:
    """Run black --check on the project. Returns exit code."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please install it via `pip install black`.", file=sys.stderr)
        return 1


def run_black_format() -> int:
    """Run black on the project to format files. Returns exit code."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: black not found. Please install it via `pip install black`.", file=sys.stderr)
        return 1


def main() -> None:
    """Main entry point for linting configuration checks and fixes."""
    print("Running Linting and Formatting Checks...")
    print("-" * 40)

    # Run Ruff Check
    print("Running Ruff Check...")
    ruff_code = run_ruff_check()
    if ruff_code != 0:
        print("Ruff check failed. Attempting to fix...")
        run_ruff_fix()

    print("-" * 40)

    # Run Black Check
    print("Running Black Check...")
    black_code = run_black_check()
    if black_code != 0:
        print("Black check failed. Formatting files...")
        run_black_format()

    print("-" * 40)
    print("Linting and Formatting configuration complete.")

    # Final status
    if ruff_code == 0 and black_code == 0:
        print("All checks passed.")
        sys.exit(0)
    else:
        print("Some issues remain. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()