"""
Script to install and configure linting/formatting tools for the project.
This script ensures flake8, black, and isort are installed and configured.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return True if successful."""
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"Stderr: {e.stderr}")
        return False

def main():
    """Main entry point for linting setup."""
    print("=== Setting up linting and formatting tools ===")

    # Check if pip is available
    if not run_command([sys.executable, "-m", "pip", "--version"], "Checking pip"):
        print("Error: pip not found. Please install pip first.")
        return 1

    # Install linting tools
    tools = [
        "flake8",
        "black",
        "isort",
        "pytest",
        "pytest-cov"
    ]

    print("\nInstalling linting and formatting tools...")
    install_cmd = [sys.executable, "-m", "pip", "install"] + tools
    if not run_command(install_cmd, "Installing linting tools"):
        print("Error: Failed to install linting tools.")
        return 1

    # Verify installation
    print("\nVerifying installation...")
    for tool in tools:
        if not run_command([sys.executable, "-m", "pip", "show", tool], f"Checking {tool}"):
            print(f"Warning: {tool} might not be installed correctly.")

    # Run initial lint check
    print("\nRunning initial flake8 check...")
    code_dir = Path(__file__).parent
    flake8_cmd = [sys.executable, "-m", "flake8", str(code_dir)]
    run_command(flake8_cmd, "Initial flake8 check")

    # Run initial black check (dry run)
    print("\nRunning initial black check (formatting check)...")
    black_cmd = [sys.executable, "-m", "black", "--check", str(code_dir)]
    run_command(black_cmd, "Initial black check")

    # Run initial isort check
    print("\nRunning initial isort check...")
    isort_cmd = [sys.executable, "-m", "isort", "--check-only", str(code_dir)]
    run_command(isort_cmd, "Initial isort check")

    print("\n=== Linting setup complete ===")
    print("\nYou can now run:")
    print("  - flake8 code/          # Run linting")
    print("  - black code/           # Format code")
    print("  - isort code/           # Sort imports")
    print("  - pytest tests/         # Run tests")

    return 0

if __name__ == "__main__":
    sys.exit(main())
