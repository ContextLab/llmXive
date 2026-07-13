"""
Script to initialize the project virtual environment and install dependencies.
This script handles the creation of .venv, activation, and pip installation
as required by task T002c.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    venv_path = project_root / ".venv"
    requirements_path = project_root / "projects" / "PROJ-517-neural-correlates-of-anticipatory-reward" / "requirements.txt"

    # Check Python version
    if sys.version_info < (3, 10):
        print(f"Error: Python 3.10+ is required. Current version: {sys.version}")
        sys.exit(1)

    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                text=True
            )
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}")
            sys.exit(1)
    else:
        print(f"Virtual environment already exists at {venv_path}.")

    # Determine the pip executable path based on OS
    if sys.platform == "win32":
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"

    if not pip_executable.exists():
        print(f"Error: pip executable not found at {pip_executable}")
        sys.exit(1)

    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            text=True
        )
        print("Pip upgraded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error upgrading pip: {e}")
        sys.exit(1)

    # Install requirements
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_path)],
            check=True,
            text=True
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

    print("Virtual environment initialization complete.")
    print(f"To activate, run: source {venv_path / 'bin' / 'activate'} (Linux/Mac)")
    print(f"or: {venv_path / 'Scripts' / 'activate'} (Windows)")

if __name__ == "__main__":
    main()
