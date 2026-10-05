"""
Setup script for linting (ruff) and formatting (black) tools.
This script initializes ruff configuration and verifies tool availability.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str], check: bool = True) -> None:
    """Run a shell command."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if check:
            sys.exit(1)

def main() -> None:
    """Initialize ruff and verify black availability."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Check if tools are installed
    print("Checking for required tools...")
    run_command([sys.executable, "-m", "black", "--version"], check=False)
    run_command([sys.executable, "-m", "ruff", "--version"], check=False)

    # Initialize ruff (creates .ruff.toml or updates pyproject.toml if present)
    # Since we already have a pyproject.toml with [tool.ruff], we just ensure it's valid
    print("\nVerifying ruff configuration...")
    run_command([sys.executable, "-m", "ruff", "check", "--output-format=concise", "."])

    print("\nVerifying black configuration...")
    run_command([sys.executable, "-m", "black", "--check", "--diff", "."])

    print("\nLinting and formatting setup complete.")
    print("To format code: black code/ tests/")
    print("To check linting: ruff check code/ tests/")

if __name__ == "__main__":
    main()