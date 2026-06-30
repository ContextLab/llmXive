"""
Project Initialization Script for llmXive
Sets up the virtual environment and installs dependencies.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Initialize the Python 3.11 project environment."""
    project_root = Path(__file__).parent
    venv_path = project_root / ".venv"
    requirements_path = project_root / "requirements.txt"

    print(f"Initializing project in: {project_root}")

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ required. Current: {sys.version}")
        sys.exit(1)

    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
    else:
        print("Virtual environment already exists.")

    # Determine the correct python executable for the venv
    if os.name == "nt":
        python_exec = venv_path / "Scripts" / "python.exe"
        pip_exec = venv_path / "Scripts" / "pip.exe"
    else:
        python_exec = venv_path / "bin" / "python"
        pip_exec = venv_path / "bin" / "pip"

    # Upgrade pip
    print("Upgrading pip...")
    subprocess.check_call([str(python_exec), "-m", "pip", "install", "--upgrade", "pip"])

    # Install dependencies
    if requirements_path.exists():
        print(f"Installing dependencies from {requirements_path}...")
        subprocess.check_call([str(pip_exec), "install", "-r", str(requirements_path)])
    else:
        print("WARNING: requirements.txt not found. Skipping dependency installation.")

    print("Project initialization complete.")
    print(f"Activate the environment with: source {venv_path / 'bin' / 'activate'}")

if __name__ == "__main__":
    main()