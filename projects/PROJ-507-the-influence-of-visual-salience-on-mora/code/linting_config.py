"""
Linting and Formatting Configuration Module.

This module provides utilities to verify, run, and configure ruff and black
for the project, ensuring code quality standards are met.
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

from config import seed_everything

# Ensure reproducibility for any internal random operations
seed_everything(42)


def verify_tools_installed() -> Tuple[bool, bool]:
    """
    Check if ruff and black are installed in the current environment.

    Returns:
        Tuple[bool, bool]: (ruff_installed, black_installed)
    """
    ruff_installed = False
    black_installed = False

    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
        ruff_installed = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
        black_installed = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    return ruff_installed, black_installed


def run_ruff_check() -> bool:
    """
    Run ruff check on the codebase.

    Returns:
        bool: True if check passes, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ruff", "check", "code/", "tests/"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ruff check failed:\n{e.stdout}")
        return False


def run_ruff_fix() -> bool:
    """
    Run ruff check with --fix to automatically resolve issues.

    Returns:
        bool: True if fix succeeds, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ruff", "check", "code/", "tests/", "--fix"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ruff fix failed:\n{e.stdout}")
        return False


def run_black_check() -> bool:
    """
    Run black --check on the codebase.

    Returns:
        bool: True if check passes, False otherwise.
    """
    try:
        result = subprocess.run(
            ["black", "--check", "code/", "tests/"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Black check failed:\n{e.stdout}")
        return False


def run_black_format() -> bool:
    """
    Run black formatter on the codebase.

    Returns:
        bool: True if format succeeds, False otherwise.
    """
    try:
        result = subprocess.run(
            ["black", "code/", "tests/"],
            check=True,
            capture_output=True,
            text=True,
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Black format failed:\n{e.stdout}")
        return False


def setup_config_files() -> bool:
    """
    Ensure configuration files (.ruff.toml, pyproject.toml) exist in the project root.
    This function is a placeholder for verification; in a real setup, these files
    should be committed to the repo. We verify their existence here.

    Returns:
        bool: True if config files exist, False otherwise.
    """
    root = Path(__file__).parent.parent
    ruff_config = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"

    if not ruff_config.exists():
        print(f"Error: {ruff_config} not found.")
        return False
    if not pyproject.exists():
        print(f"Error: {pyproject} not found.")
        return False

    print("Configuration files verified.")
    return True


def main() -> None:
    """
    Main entry point for linting configuration verification and execution.
    """
    print("=== Linting & Formatting Configuration ===")

    # Verify tools
    ruff_ok, black_ok = verify_tools_installed()
    if not ruff_ok or not black_ok:
        print("Missing required tools:")
        if not ruff_ok:
            print("  - ruff is not installed. Install with: pip install ruff")
        if not black_ok:
            print("  - black is not installed. Install with: pip install black")
        sys.exit(1)

    print("Tools verified: ruff and black are installed.")

    # Verify config files
    if not setup_config_files():
        print("Configuration files missing. Please ensure .ruff.toml and pyproject.toml exist.")
        sys.exit(1)

    # Run checks
    print("\n--- Running Ruff Check ---")
    if not run_ruff_check():
        print("Ruff check failed. Attempting fix...")
        run_ruff_fix()
        # Re-check after fix
        if not run_ruff_check():
            print("Ruff check still failed after fix.")
        else:
            print("Ruff check passed after fix.")

    print("\n--- Running Black Check ---")
    if not run_black_check():
        print("Black check failed. Formatting...")
        run_black_format()
        # Re-check after format
        if not run_black_check():
            print("Black check still failed after format.")
        else:
            print("Black check passed after format.")

    print("\n=== Linting & Formatting Complete ===")


if __name__ == "__main__":
    main()
