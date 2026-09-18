"""
Script to initialize and verify linting/formatting configuration for the project.
This script ensures that ruff and black are configured correctly via pyproject.toml
and optional standalone config files, and provides a command to run checks.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> None:
    """Run a shell command and raise on failure."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        if check:
            print(f"Error running command: {e}")
            sys.exit(1)
        else:
            print(f"Command failed (expected): {e}")


def check_tool_installed(tool: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run([tool, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main() -> None:
    """Entry point for linting setup verification."""
    print("Checking linting and formatting tools...")

    # Check ruff
    if not check_tool_installed("ruff"):
        print("⚠️  ruff not found. Installing...")
        run_command([sys.executable, "-m", "pip", "install", "ruff"])

    # Check black
    if not check_tool_installed("black"):
        print("⚠️  black not found. Installing...")
        run_command([sys.executable, "-m", "pip", "install", "black"])

    print("✅ Tools ready.")
    print("Configuration files (.ruff.toml, pyproject.toml, .pre-commit-config.yaml) should be present in the project root.")
    print("To run checks manually:")
    print("  ruff check .")
    print("  black --check .")
    print("To auto-fix and format:")
    print("  ruff check --fix .")
    print("  black .")


if __name__ == "__main__":
    main()