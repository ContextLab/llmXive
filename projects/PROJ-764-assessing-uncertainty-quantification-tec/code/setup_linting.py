"""
Setup script to install linting (ruff) and formatting (black) tools.
This script ensures the required dependencies are present and provides
a command to run the pre-commit hooks.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    """Main entry point for setup_linting.py."""
    print("Setting up linting and formatting tools...")

    # Ensure we are in the code directory
    code_dir = Path(__file__).parent
    if not code_dir.exists():
        print(f"Error: Code directory {code_dir} does not exist.")
        sys.exit(1)

    # Install ruff and black
    print("Installing ruff and black...")
    run_command([sys.executable, "-m", "pip", "install", "ruff", "black", "pre-commit"])

    # Install pre-commit hooks
    print("Installing pre-commit hooks...")
    run_command([sys.executable, "-m", "pre_commit", "install"])

    print("Setup complete. Run 'pre-commit run --all-files' to check all files.")

if __name__ == "__main__":
    main()
