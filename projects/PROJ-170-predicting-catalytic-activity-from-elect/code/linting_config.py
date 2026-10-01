"""
Linting and Formatting Configuration Management.
Provides utilities to ensure Black and Ruff configurations are present
and to run checks/formatting against the codebase.
"""
import os
import sys
import subprocess
from pathlib import Path

from config import get_project_root


def ensure_linting_config() -> bool:
    """
    Verify that pyproject.toml (Black) and .ruff.toml exist in the project root.
    Returns True if both exist, False otherwise.
    """
    root = get_project_root()
    black_config = root / "pyproject.toml"
    ruff_config = root / ".ruff.toml"

    if not black_config.exists():
        print(f"ERROR: Black config not found at {black_config}")
        return False
    if not ruff_config.exists():
        print(f"ERROR: Ruff config not found at {ruff_config}")
        return False
    return True


def run_black_check() -> int:
    """
    Run 'black --check .' using the project's pyproject.toml.
    Returns the subprocess exit code.
    """
    print("Running Black check...")
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=get_project_root(),
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print("ERROR: 'black' command not found. Please install it.")
        return 1


def run_ruff_check() -> int:
    """
    Run 'ruff check .' using the project's .ruff.toml.
    Returns the subprocess exit code.
    """
    print("Running Ruff check...")
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=get_project_root(),
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print("ERROR: 'ruff' command not found. Please install it.")
        return 1


def run_black_format() -> int:
    """
    Run 'black .' to format the codebase.
    Returns the subprocess exit code.
    """
    print("Running Black formatter...")
    try:
        result = subprocess.run(
            ["black", "."],
            cwd=get_project_root(),
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print("ERROR: 'black' command not found. Please install it.")
        return 1


def run_ruff_fix() -> int:
    """
    Run 'ruff check --fix .' to automatically fix linting issues.
    Returns the subprocess exit code.
    """
    print("Running Ruff fix...")
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", "."],
            cwd=get_project_root(),
            capture_output=False,
            text=True
        )
        return result.returncode
    except FileNotFoundError:
        print("ERROR: 'ruff' command not found. Please install it.")
        return 1


def main():
    """
    Main entry point for linting configuration verification and execution.
    Verifies configs exist, then runs checks.
    """
    if not ensure_linting_config():
        print("Linting configuration verification failed.")
        sys.exit(1)

    print("Configuration files found. Running checks...")

    # Run Black check
    black_code = run_black_check()
    if black_code != 0:
        print("Black check failed. Run 'black .' to format.")
    else:
        print("Black check passed.")

    # Run Ruff check
    ruff_code = run_ruff_check()
    if ruff_code != 0:
        print("Ruff check failed. Run 'ruff check --fix .' to fix.")
    else:
        print("Ruff check passed.")

    if black_code != 0 or ruff_code != 0:
        sys.exit(1)
    else:
        print("All linting and formatting checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()