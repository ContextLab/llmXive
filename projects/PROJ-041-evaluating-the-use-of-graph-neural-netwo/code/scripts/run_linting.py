"""
Script to run linting and formatting checks on the project codebase.
This script provides a convenient way to run ruff and black without
needing to remember the exact command-line arguments.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).resolve().parent.parent,
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Command '{cmd[0]}' not found. Please install the required tools.")
        return False

def main() -> int:
    """Main entry point for the linting script."""
    code_dir = Path(__file__).resolve().parent.parent

    print("Running linting and formatting checks...")
    print(f"Project root: {code_dir}")

    # Check if tools are installed
    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
        print("✓ Ruff is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Ruff is not installed. Install with: pip install ruff")
        return 1

    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
        print("✓ Black is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Black is not installed. Install with: pip install black")
        return 1

    success = True

    # Run ruff check
    if not run_command(
        ["ruff", "check", str(code_dir), "--config", str(code_dir / ".ruff.toml")],
        "Ruff linting"
    ):
        print("⚠ Ruff found issues. Run 'ruff check . --fix' to auto-fix some.")
        success = False

    # Run black check
    if not run_command(
        ["black", "--check", str(code_dir), "--config", str(code_dir / ".black.toml")],
        "Black formatting check"
    ):
        print("⚠ Black found formatting issues. Run 'black .' to fix.")
        success = False

    print(f"\n{'='*60}")
    if success:
        print("✓ All linting and formatting checks passed!")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
    print(f"{'='*60}")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
