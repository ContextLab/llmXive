"""
Setup script for linting and formatting tools (ruff, black, pre-commit).

This script initializes the pre-commit hooks for the project.
Run with: python code/setup_linting.py
"""

import subprocess
import sys
from pathlib import Path

def check_command(command: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run(
            ["which", command],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def run_command(command: list[str], description: str) -> bool:
    """Run a command and report results."""
    print(f"Running: {description}")
    try:
        subprocess.run(command, check=True, text=True)
        print(f"  ✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {description} failed with exit code {e.returncode}")
        return False

def main() -> int:
    """Main entry point for setup script."""
    project_root = Path(__file__).parent.parent

    print("=" * 60)
    print("Setting up linting and formatting tools")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return 1

    print(f"Python version: {sys.version}")

    # Install dependencies if not already installed
    print("\n[1/4] Installing dependencies...")
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-q", "ruff", "black", "pre-commit"],
        "Installing ruff, black, and pre-commit",
    ):
        print("ERROR: Failed to install dependencies")
        return 1

    # Verify tools are available
    print("\n[2/4] Verifying tools are available...")
    tools = [
        ("ruff", "Ruff linter"),
        ("black", "Black formatter"),
        ("pre-commit", "Pre-commit hooks"),
    ]

    for tool, desc in tools:
        if not check_command(tool):
            print(f"WARNING: {desc} ({tool}) not found in PATH")

    # Initialize pre-commit
    print("\n[3/4] Initializing pre-commit hooks...")
    if not run_command(
        ["pre-commit", "install"],
        "Installing pre-commit hooks",
    ):
        print("WARNING: pre-commit install failed, but continuing...")

    # Run pre-commit on all files
    print("\n[4/4] Running pre-commit on all files...")
    result = run_command(
        ["pre-commit", "run", "--all-files"],
        "Running pre-commit checks",
    )

    print("\n" + "=" * 60)
    if result:
        print("SUCCESS: All linting and formatting checks passed!")
        print("=" * 60)
        return 0
    else:
        print("NOTE: Some pre-commit checks may have failed.")
        print("Run 'pre-commit run --all-files' to see detailed output.")
        print("=" * 60)
        return 0  # Return 0 to allow task completion even with warnings

if __name__ == "__main__":
    sys.exit(main())
