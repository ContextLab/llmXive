import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """Return the project root directory path."""
    # Assuming the script is run from the project root or code directory
    current = Path.cwd()
    # Look for the specific project directory
    project_name = "PROJ-871-llmxive-follow-up-extending-planbench-xl"
    if current.name == project_name:
        return current
    parent = current.parent
    while parent != parent.parent:
        if parent.name == project_name:
            return parent
        current = parent
        parent = current.parent
    # Fallback: assume current is root if not found in hierarchy
    return current

def main():
    """Initialize a Python virtual environment and install dependencies."""
    project_root = get_project_root()
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Project root: {project_root}")
    print(f"Virtual environment path: {venv_path}")

    # Create virtual environment
    if not venv_path.exists():
        print("Creating virtual environment...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment already exists.")

    # Determine the python executable in the venv
    if os.name == "nt":  # Windows
        python_executable = venv_path / "Scripts" / "python.exe"
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/Mac
        python_executable = venv_path / "bin" / "python"
        pip_executable = venv_path / "bin" / "pip"

    # Upgrade pip
    print("Upgrading pip...")
    try:
        subprocess.check_call([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to upgrade pip: {e}")

    # Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.check_call([str(pip_executable), "install", "-r", str(requirements_path)])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

    print("Virtual environment setup and dependency installation complete.")

if __name__ == "__main__":
    main()
