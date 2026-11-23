"""
Setup script to install and configure linting (ruff) and formatting (black) tools.
This script ensures that the project follows the defined style guidelines.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command: list, check: bool = True) -> None:
    """Run a shell command and print it."""
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=check, shell=False)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        if check:
            sys.exit(1)

def main():
    """Main entry point for T003: Configure linting and formatting."""
    print("Starting T003: Configuring linting (ruff) and formatting (black)...")
    
    # Verify installation of tools
    run_command([sys.executable, "-m", "pip", "install", "-e", "."])
    
    # Verify Ruff configuration
    print("\n1. Verifying Ruff configuration (pyproject.toml)...")
    ruff_config_path = Path("pyproject.toml")
    if not ruff_config_path.exists():
        print("ERROR: pyproject.toml not found. Please ensure it exists in the project root.")
        sys.exit(1)
    
    # Run ruff check to validate code style
    print("2. Running 'ruff check' to validate code style...")
    run_command([sys.executable, "-m", "ruff", "check", "code/"])
    
    # Run ruff format check (or black check if ruff format not available)
    print("3. Running 'black --check' to validate formatting...")
    run_command([sys.executable, "-m", "black", "--check", "code/"])
    
    print("\nT003 Complete: Linting and formatting tools are configured and validated.")
    print("To fix issues automatically, run: ruff check --fix code/ && black code/")

if __name__ == "__main__":
    main()
