"""
Script to initialize the Python 3.11 virtual environment for the project.
This script creates a virtual environment in the project root and installs
dependencies from code/requirements.txt.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "code" / "requirements.txt"

    print(f"Project root: {project_root}")
    print(f"Requirements file: {requirements_path}")

    if not requirements_path.exists():
        print(f"ERROR: Requirements file not found at {requirements_path}")
        sys.exit(1)

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"WARNING: Python version {sys.version_info.major}.{sys.version_info.minor} detected.")
        print("This project requires Python 3.11. The virtual environment creation may fail or produce unexpected results.")
    
    # Remove existing venv if present
    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}...")
        shutil.rmtree(venv_path)

    # Create virtual environment
    print(f"Creating virtual environment at {venv_path}...")
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

    # Determine the pip executable path based on OS
    if os.name == 'nt':
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"

    if not pip_executable.exists():
        print(f"ERROR: pip executable not found at {pip_executable}")
        sys.exit(1)

    # Upgrade pip
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Pip upgraded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to upgrade pip: {e.stderr.decode()}")

    # Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e.stderr.decode()}")
        sys.exit(1)

    print("\nVirtual environment setup complete.")
    print(f"Activate the environment using:")
    if os.name == 'nt':
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()