"""
Script to initialize linting and formatting tools (Ruff, Black).
This script ensures the tools are installed and configuration files are in place.
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and report status."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False


def main() -> int:
    """Main entry point for setup_linting."""
    project_root = Path(__file__).parent
    config_file = project_root / "pyproject.toml"

    if not config_file.exists():
        print("Error: pyproject.toml not found in project root.")
        print("Please run this script from the 'code' directory or ensure pyproject.toml exists.")
        return 1

    # Check if ruff is installed
    if not run_command([sys.executable, "-m", "pip", "show", "ruff"], "Checking Ruff installation"):
        print("Installing Ruff...")
        if not run_command([sys.executable, "-m", "pip", "install", "ruff"], "Installing Ruff"):
            print("Failed to install Ruff.")
            return 1

    # Check if black is installed
    if not run_command([sys.executable, "-m", "pip", "show", "black"], "Checking Black installation"):
        print("Installing Black...")
        if not run_command([sys.executable, "-m", "pip", "install", "black"], "Installing Black"):
            print("Failed to install Black.")
            return 1

    print("\nConfiguration found in pyproject.toml.")
    print("Tools (Ruff, Black) are ready to use.")
    print("\nUsage:")
    print("  Check code: ruff check code/")
    print("  Format code: black code/")
    print("  Check and fix: ruff check --fix code/")

    return 0


if __name__ == "__main__":
    sys.exit(main())