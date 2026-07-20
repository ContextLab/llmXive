"""
Script to initialize the Python 3.11 virtual environment and install dependencies.
This script fulfills the 'run' part of T002.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    venv_dir = project_root / "venv"
    requirements_file = project_root / "requirements.txt"

    print(f"Project root: {project_root}")
    print(f"Requirements file: {requirements_file}")

    if not requirements_file.exists():
        print("ERROR: requirements.txt not found. Please run this from the project root.")
        sys.exit(1)

    # Check Python version (3.11)
    python_version = sys.version_info
    print(f"Current Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version.major != 3 or python_version.minor < 11:
        print("WARNING: This project targets Python 3.11. Proceeding with current interpreter.")
    
    # Remove existing venv if it exists to ensure clean state
    if venv_dir.exists():
        print(f"Removing existing virtual environment at {venv_dir}...")
        shutil.rmtree(venv_dir)

    # Create virtual environment
    print(f"Creating virtual environment at {venv_dir}...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

    # Determine the pip path based on OS
    if os.name == 'nt':
        pip_executable = venv_dir / "Scripts" / "pip.exe"
        python_executable = venv_dir / "Scripts" / "python.exe"
    else:
        pip_executable = venv_dir / "bin" / "pip"
        python_executable = venv_dir / "bin" / "python"

    if not pip_executable.exists():
        print(f"ERROR: pip not found at {pip_executable}")
        sys.exit(1)

    # Upgrade pip first
    print("Upgrading pip...")
    subprocess.run([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"], check=True)

    # Install requirements
    print(f"Installing dependencies from {requirements_file}...")
    try:
        subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_file)],
            check=True
        )
        print("SUCCESS: All dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies. Exit code: {e.returncode}")
        sys.exit(1)

if __name__ == "__main__":
    main()