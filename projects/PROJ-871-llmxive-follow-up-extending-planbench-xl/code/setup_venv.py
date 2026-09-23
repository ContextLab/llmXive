"""
Virtual Environment Setup Script for llmXive Project.

This script handles the creation of a Python virtual environment,
installation of dependencies from requirements.txt, and verification.
"""
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """Get the root directory of the project."""
    # The script is located at code/setup_venv.py, so root is parent of parent
    return Path(__file__).resolve().parent.parent

def create_venv(venv_path: Path) -> bool:
    """
    Create a Python virtual environment at the specified path.

    Args:
        venv_path: Path where the virtual environment should be created.

    Returns:
        True if successful, False otherwise.
    """
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return True

    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e.stderr}")
        return False

def install_dependencies(venv_path: Path, requirements_path: Path) -> bool:
    """
    Install dependencies from requirements.txt into the virtual environment.

    Args:
        venv_path: Path to the virtual environment.
        requirements_path: Path to the requirements.txt file.

    Returns:
        True if successful, False otherwise.
    """
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False

    # Determine the pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print(f"Error: pip not found in virtual environment at {pip_path}")
        return False

    print(f"Installing dependencies from {requirements_path}...")
    try:
        # Upgrade pip first
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True
        )

        # Install requirements
        result = subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e.stderr}")
        return False

def verify_venv(venv_path: Path) -> bool:
    """
    Verify the virtual environment is functional.

    Args:
        venv_path: Path to the virtual environment.

    Returns:
        True if verification passes, False otherwise.
    """
    if os.name == 'nt':  # Windows
        python_path = venv_path / "Scripts" / "python.exe"
    else:  # Unix/Linux/macOS
        python_path = venv_path / "bin" / "python"

    if not python_path.exists():
        print(f"Error: Python executable not found at {python_path}")
        return False

    print("Verifying virtual environment...")
    try:
        # Check Python version
        result = subprocess.run(
            [str(python_path), "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Python version: {result.stdout.strip()}")

        # Check pip list
        result = subprocess.run(
            [str(python_path), "-m", "pip", "list"],
            check=True,
            capture_output=True,
            text=True
        )
        print("Installed packages:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Verification failed: {e.stderr}")
        return False

def main():
    """Main entry point for the setup script."""
    project_root = get_project_root()
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    print(f"Project Root: {project_root}")
    print(f"Virtual Environment Path: {venv_path}")
    print(f"Requirements Path: {requirements_path}")
    print("-" * 50)

    # Step 1: Create venv
    if not create_venv(venv_path):
        print("ERROR: Failed to create virtual environment.")
        sys.exit(1)

    # Step 2: Install dependencies
    if not install_dependencies(venv_path, requirements_path):
        print("ERROR: Failed to install dependencies.")
        sys.exit(1)

    # Step 3: Verify
    if not verify_venv(venv_path):
        print("ERROR: Failed to verify virtual environment.")
        sys.exit(1)

    print("-" * 50)
    print("Setup completed successfully!")
    print(f"To activate the environment, run:")
    if os.name == 'nt':
        print(f"  {venv_path}\\Scripts\\activate.bat")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()