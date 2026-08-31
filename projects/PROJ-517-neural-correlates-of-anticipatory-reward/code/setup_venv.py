"""
Virtual Environment Initialization Script for PROJ-517.

This script automates the creation of a Python virtual environment in the project root
and installs dependencies from requirements.txt.

It ensures Python 3.10+ is used and handles the installation process robustly.
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize the virtual environment and install dependencies.

    Steps:
    1. Verify Python version is 3.10 or higher.
    2. Create a .venv directory in the project root if it doesn't exist.
    3. Install packages from requirements.txt into the virtual environment.
    """
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / ".venv"
    requirements_path = project_root / "projects" / "PROJ-517-neural-correlates-of-anticipatory-reward" / "requirements.txt"

    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    # Check Python version
    if sys.version_info < (3, 10):
        print(f"ERROR: Python 3.10+ is required. Current version: {sys.version}")
        sys.exit(1)

    print(f"Project Root: {project_root}")
    print(f"Virtual Environment Target: {venv_path}")
    print(f"Requirements File: {requirements_path}")

    # Create virtual environment
    if venv_path.exists():
        print("Virtual environment already exists. Removing it to ensure a clean state...")
        import shutil
        shutil.rmtree(venv_path)

    print("Creating virtual environment...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e.stderr.decode()}")
        sys.exit(1)

    # Determine the path to pip within the virtual environment
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"

    if not pip_path.exists():
        print(f"ERROR: pip not found at {pip_path}")
        sys.exit(1)

    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to upgrade pip: {e.stderr.decode()}")
        # Continue anyway, as older pip might still work

    # Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e.stderr.decode()}")
        sys.exit(1)

    print("\nSetup complete.")
    print(f"To activate the environment, run:")
    if sys.platform == "win32":
        print(f"  .venv\\Scripts\\activate")
    else:
        print(f"  source .venv/bin/activate")

    return 0

if __name__ == "__main__":
    sys.exit(main())
