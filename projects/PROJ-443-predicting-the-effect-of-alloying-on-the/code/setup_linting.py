"""
Setup script to verify and initialize linting and formatting tools.

This script checks for the presence of flake8, black, and pre-commit,
and provides installation instructions if they are missing.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_command(command: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_dev_dependencies():
    """Install development dependencies including linting tools."""
    print("Installing development dependencies (flake8, black, isort, pre-commit)...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-e", ".[dev]"],
            cwd=Path(__file__).parent.parent,
        )
        print("Development dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}", file=sys.stderr)
        sys.exit(1)

def setup_pre_commit():
    """Initialize pre-commit hooks if not already installed."""
    print("Checking pre-commit installation...")
    if not check_command("pre-commit"):
        print("pre-commit is not installed. Installing...")
        install_dev_dependencies()
    
    print("Installing pre-commit hooks...")
    try:
        subprocess.check_call(["pre-commit", "install"])
        print("Pre-commit hooks installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing pre-commit hooks: {e}", file=sys.stderr)
        sys.exit(1)

def verify_linting_tools():
    """Verify that all required linting tools are available."""
    tools = {
        "flake8": "flake8",
        "black": "black",
        "isort": "isort",
        "pre-commit": "pre-commit",
    }
    
    missing = []
    for name, command in tools.items():
        if not check_command(command):
            missing.append(name)
    
    if missing:
        print(f"Missing linting tools: {', '.join(missing)}")
        print("\nTo install all tools, run: pip install -e '.[dev]'")
        print("Or install individual tools:")
        for tool in missing:
            print(f"  pip install {tool}")
        return False
    
    print("All linting tools are available.")
    return True

def main():
    """Main entry point for the setup script."""
    print("Setting up linting and formatting tools for HEA Elastic Modulus project...")
    
    # Verify tools first
    if not verify_linting_tools():
        print("\nTools missing. Attempting to install dev dependencies...")
        install_dev_dependencies()
        
        if not verify_linting_tools():
            print("\nFailed to install required tools. Please check your environment.")
            sys.exit(1)
    
    # Setup pre-commit
    setup_pre_commit()
    
    print("\nLinting and formatting setup complete!")
    print("\nUsage:")
    print("  - Run 'black code/' to format all Python files")
    print("  - Run 'flake8 code/' to check for style violations")
    print("  - Run 'pre-commit run --all-files' to run all hooks")
    print("  - Add 'pre-commit install' to run hooks on every commit")

if __name__ == "__main__":
    main()
