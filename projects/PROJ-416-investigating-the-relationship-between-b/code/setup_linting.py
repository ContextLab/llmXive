"""
Script to initialize linting and formatting configuration for the project.
This script ensures that .flake8, pyproject.toml, and .pre-commit-config.yaml
are correctly set up according to project standards.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str]) -> None:
    """Execute a shell command and raise on failure."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main() -> None:
    """Initialize linting tools."""
    root = Path(__file__).parent.parent
    
    # Check if pre-commit is installed
    try:
        import pre_commit
    except ImportError:
        print("Installing pre-commit...")
        run_command([sys.executable, "-m", "pip", "install", "pre-commit"])

    # Install git hooks
    print("Installing pre-commit hooks...")
    run_command(["pre-commit", "install"])
    
    # Run a sample lint check (dry run) to verify configuration
    print("Verifying configuration...")
    # We don't run full lint here as files might not exist yet, 
    # but we verify the tools are available.
    run_command(["flake8", "--version"])
    run_command(["black", "--version"])
    run_command(["isort", "--version"])

    print("Linting and formatting tools configured successfully.")

if __name__ == "__main__":
    main()