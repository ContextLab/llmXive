"""
Script to verify and setup linting and formatting tools.
This script ensures that ruff, black, and pre-commit are installed
and configured correctly for the project.
"""
import os
import sys
import subprocess
from pathlib import Path

def check_command(cmd):
    """Check if a command is available."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_if_missing(package):
    """Install a package if it's missing."""
    if not check_command(package.split(" ")[0].split("=")[0]):
        print(f"Installing {package}...")
        subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)

def main():
    """Main entry point."""
    print("Setting up linting and formatting tools...")
    
    # Ensure tools are installed
    install_if_missing("ruff")
    install_if_missing("black")
    install_if_missing("pre-commit")
    
    # Verify configuration files exist
    project_root = Path(__file__).resolve().parent.parent
    config_files = [
        project_root / ".ruff.toml",
        project_root / "pyproject.toml",
        project_root / ".pre-commit-config.yaml",
    ]
    
    for config_file in config_files:
        if not config_file.exists():
            print(f"ERROR: Configuration file missing: {config_file}")
            sys.exit(1)
        print(f"Found configuration: {config_file}")
    
    # Initialize pre-commit if not already done
    try:
        subprocess.run(
            ["pre-commit", "install"],
            cwd=project_root,
            check=True,
            capture_output=True
        )
        print("Pre-commit hooks installed successfully.")
    except subprocess.CalledProcessError:
        print("Warning: Could not install pre-commit hooks. You may need to run 'pre-commit install' manually.")
    
    print("Linting and formatting setup complete.")
    print("Run 'pre-commit run --all-files' to check all files.")

if __name__ == "__main__":
    main()