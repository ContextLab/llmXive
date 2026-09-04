"""
Setup script to initialize linting and formatting configuration.
This script ensures that pyproject.toml is correctly configured for ruff and black,
and provides a helper to run checks.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], description: str) -> bool:
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
        print(f"Error in {description}: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def main():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    pyproject_path = code_dir / "pyproject.toml"

    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found. Please run setup_requirements.py first.")
        sys.exit(1)

    print(f"Configuring linting tools in: {code_dir}")

    # Check if ruff is installed
    if not run_command([sys.executable, "-m", "pip", "show", "ruff"], "Checking ruff installation"):
        print("Installing ruff...")
        if not run_command([sys.executable, "-m", "pip", "install", "ruff"], "Installing ruff"):
            sys.exit(1)

    # Check if black is installed
    if not run_command([sys.executable, "-m", "pip", "show", "black"], "Checking black installation"):
        print("Installing black...")
        if not run_command([sys.executable, "-m", "pip", "install", "black"], "Installing black"):
            sys.exit(1)

    print("\nLinting and formatting configuration complete.")
    print("\nTo format code:")
    print(f"  {sys.executable} -m black {code_dir}")
    print("\nTo lint code:")
    print(f"  {sys.executable} -m ruff check {code_dir}")
    print("\nTo fix linting errors automatically:")
    print(f"  {sys.executable} -m ruff check --fix {code_dir}")

if __name__ == "__main__":
    main()
