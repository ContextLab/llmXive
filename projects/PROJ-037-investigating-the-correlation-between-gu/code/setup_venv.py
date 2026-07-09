"""
T002b: Create virtual environment and install requirements.

This script automates the creation of a Python virtual environment in the project root
and installs all dependencies listed in requirements.txt.

Usage:
    python code/setup_venv.py
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and raise an error if it fails."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=cwd)
        print("Success.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return False

def main():
    # Determine project root (parent of 'code' directory)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: {requirements_path} not found.")
        sys.exit(1)

    # Remove existing venv if present
    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}...")
        shutil.rmtree(venv_path)

    # Create virtual environment
    print(f"Creating virtual environment at {venv_path}...")
    if not run_command([sys.executable, "-m", "venv", str(venv_path)]):
        print("Failed to create virtual environment.")
        sys.exit(1)

    # Determine the path to the pip executable inside the venv
    if os.name == "nt":  # Windows
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"

    if not pip_executable.exists():
        print(f"Error: pip not found at {pip_executable}")
        sys.exit(1)

    # Upgrade pip first
    print("Upgrading pip...")
    if not run_command([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"]):
        print("Warning: Failed to upgrade pip, proceeding with installation.")

    # Install requirements
    print(f"Installing requirements from {requirements_path}...")
    if not run_command([str(pip_executable), "install", "-r", str(requirements_path)]):
        print("Failed to install requirements.")
        sys.exit(1)

    print("Virtual environment setup complete.")
    print(f"Activate the environment using: source venv/bin/activate (Unix) or venv\\Scripts\\activate (Windows)")

if __name__ == "__main__":
    main()
