"""
Script to create a Python virtual environment for the project.
Executes: python3.11 -m venv venv
"""
import os
import subprocess
import sys
from pathlib import Path


def main():
    """Create the virtual environment in the repository root."""
    root_dir = Path(__file__).resolve().parent.parent
    venv_path = root_dir / "venv"

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return

    python_executable = sys.executable
    # Ensure we are using python 3.11 if available, otherwise fall back to current
    # The task specifically requested python3.11
    if "3.11" not in python_executable:
        # Try to find python3.11 explicitly
        try:
            subprocess.run(["python3.11", "--version"], check=True, capture_output=True)
            python_executable = "python3.11"
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Warning: python3.11 not found in PATH. Using current interpreter.")
            print(f"Current interpreter: {python_executable}")

    print(f"Creating virtual environment at {venv_path} using {python_executable}...")
    try:
        result = subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Virtual environment created successfully.")
        print(f"Activate it with: source {venv_path / 'bin' / 'activate'} (Linux/Mac)")
        print(f"Activate it with: {venv_path / 'Scripts' / 'activate.bat'} (Windows)")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    main()