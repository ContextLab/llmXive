"""
Configure linting (ruff) and formatting (black) tools for the project.

This script ensures that the configuration files are present and valid.
It can be run to verify the setup or to initialize the tools if needed.
"""
import os
import json
import subprocess
import sys
from pathlib import Path

def check_command_exists(command: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_command(cmd: list) -> None:
    """Run a shell command and print the output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main() -> None:
    """Main entry point for configuring linting and formatting tools."""
    project_root = Path(__file__).parent
    config_file = project_root / "pyproject.toml"

    if not config_file.exists():
        print("Error: pyproject.toml not found. Please ensure the project is initialized.")
        sys.exit(1)

    print("Checking for Black and Ruff...")

    if not check_command_exists("black"):
        print("Black is not installed. Installing with pip...")
        run_command([sys.executable, "-m", "pip", "install", "black"])
    
    if not check_command_exists("ruff"):
        print("Ruff is not installed. Installing with pip...")
        run_command([sys.executable, "-m", "pip", "install", "ruff"])

    print("Verifying configuration files...")
    
    # Verify pyproject.toml contains tool configurations
    with open(config_file, "r") as f:
        content = f.read()
        if "[tool.black]" not in content:
            print("Warning: [tool.black] section not found in pyproject.toml")
        if "[tool.ruff]" not in content:
            print("Warning: [tool.ruff] section not found in pyproject.toml")

    print("Running Black check (dry-run)...")
    run_command(["black", "--check", "--diff", str(project_root)])

    print("Running Ruff check...")
    run_command(["ruff", "check", str(project_root)])

    print("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()