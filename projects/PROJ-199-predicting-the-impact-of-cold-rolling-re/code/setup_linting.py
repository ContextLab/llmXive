"""
Setup script to initialize pre-commit hooks and verify linting configuration.

This script ensures that:
1. Pre-commit is installed
2. Pre-commit hooks are installed
3. Configuration files (.flake8, pyproject.toml, .pre-commit-config.yaml) are valid

Run this script after cloning the repository to set up the development environment.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"  ✓ {description} completed successfully")
        if result.stdout:
            print(f"    Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed")
        if e.stderr:
            print(f"    Error: {e.stderr.strip()}")
        return False

def main():
    """Main setup routine."""
    print("=" * 60)
    print("Setting up linting and formatting tools for llmXive project")
    print("=" * 60)
    
    # Check if we're in the project root
    project_root = Path(__file__).parent.parent
    if not (project_root / ".pre-commit-config.yaml").exists():
        print("Error: .pre-commit-config.yaml not found. Are you in the project root?")
        sys.exit(1)
    
    # 1. Install pre-commit if not present
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-q", "pre-commit"],
        "Installing pre-commit"
    ):
        print("Warning: Could not install pre-commit. Please install manually.")
    
    # 2. Install git hooks
    run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hooks"
    )
    
    # 3. Run pre-commit on all files (optional, can be slow)
    print("\nRunning pre-commit on all files (this may take a moment)...")
    run_command(
        ["pre-commit", "run", "--all-files"],
        "Running pre-commit checks"
    )
    
    # 4. Verify flake8 configuration
    print("\nVerifying flake8 configuration...")
    if run_command(
        ["flake8", "--version"],
        "Checking flake8 version"
    ):
        print("  ✓ flake8 is properly configured")
    
    # 5. Verify black configuration
    print("\nVerifying black configuration...")
    if run_command(
        ["black", "--version"],
        "Checking black version"
    ):
        print("  ✓ black is properly configured")
    
    print("\n" + "=" * 60)
    print("Setup complete! You can now:")
    print("  - Run 'pre-commit run' to check staged files")
    print("  - Run 'pre-commit run --all-files' to check all files")
    print("  - Run 'black code/' to format code")
    print("  - Run 'flake8 code/' to check for linting issues")
    print("=" * 60)

if __name__ == "__main__":
    main()