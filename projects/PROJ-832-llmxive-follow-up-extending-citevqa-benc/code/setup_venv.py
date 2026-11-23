"""
Task T002b: Set up Python virtual environment and install requirements.

This script creates a virtual environment named 'venv' in the project root
and installs all dependencies from requirements.txt.
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def main():
    """Create venv and install requirements."""
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    print(f"Project root: {project_root}")
    print(f"Virtual environment path: {venv_path}")
    print(f"Requirements file: {requirements_path}")

    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        print("Please ensure T002a has been completed to create requirements.txt.")
        sys.exit(1)

    # Remove existing venv if present
    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}...")
        shutil.rmtree(venv_path)

    # Create virtual environment
    print("Creating virtual environment...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment: {e.stderr.decode()}")
        sys.exit(1)

    # Determine the Python executable in the venv
    if os.name == "nt":  # Windows
        pip_executable = venv_path / "Scripts" / "pip.exe"
        python_executable = venv_path / "Scripts" / "python.exe"
    else:  # Unix/macOS
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"

    # Upgrade pip first
    print("Upgrading pip...")
    try:
        subprocess.run(
            [str(python_executable), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("pip upgraded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"WARNING: Failed to upgrade pip: {e.stderr.decode()}")
        # Continue anyway, as we still need to install requirements

    # Install requirements
    print("Installing requirements from requirements.txt...")
    try:
        subprocess.run(
            [str(pip_executable), "install", "-r", str(requirements_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install requirements: {e.stderr.decode()}")
        print("Please check requirements.txt for invalid package names or versions.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Virtual environment setup complete!")
    print(f"To activate the environment, run:")
    if os.name == "nt":
        print(f"  venv\\Scripts\\activate")
    else:
        print(f"  source venv/bin/activate")
    print("=" * 50)

if __name__ == "__main__":
    main()
