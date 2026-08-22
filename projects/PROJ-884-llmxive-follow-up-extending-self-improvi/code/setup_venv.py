"""
Setup script for creating a Python virtual environment and installing dependencies.
This script handles the initialization of the venv and dependency installation
for the llmXive research pipeline.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

# Ensure we are in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_ROOT / "venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

def find_python311():
    """
    Find a Python 3.11 executable.
    Tries common versioned names and the generic python3.
    """
    candidates = ["python3.11", "python3", "python"]
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            if "3.11" in result.stdout:
                return candidate
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return None

def create_virtual_environment():
    """
    Create a virtual environment in the specified directory.
    """
    if not VENV_DIR.exists():
        print(f"Creating virtual environment at {VENV_DIR}...")
        python_exe = find_python311()
        if not python_exe:
            raise RuntimeError(
                "Could not find Python 3.11. Please install Python 3.11 "
                "or set the PYTHON environment variable."
            )
        
        subprocess.run(
            [python_exe, "-m", "venv", str(VENV_DIR)],
            check=True
        )
        print("Virtual environment created successfully.")
    else:
        print(f"Virtual environment already exists at {VENV_DIR}.")

def install_dependencies():
    """
    Install dependencies from requirements.txt into the virtual environment.
    """
    if not REQUIREMENTS_FILE.exists():
        print(f"Warning: {REQUIREMENTS_FILE} not found. Skipping dependency installation.")
        return

    print("Installing dependencies...")
    pip_executable = VENV_DIR / "bin" / "pip"
    if sys.platform == "win32":
        pip_executable = VENV_DIR / "Scripts" / "pip"

    subprocess.run(
        [str(pip_executable), "install", "--upgrade", "pip"],
        check=True
    )
    
    subprocess.run(
        [str(pip_executable), "install", "-r", str(REQUIREMENTS_FILE)],
        check=True
    )
    print("Dependencies installed successfully.")

def main():
    """
    Main entry point for the setup script.
    """
    try:
        create_virtual_environment()
        install_dependencies()
        print("Setup complete.")
        print(f"Activate the environment with: source {VENV_DIR}/bin/activate")
    except subprocess.CalledProcessError as e:
        print(f"Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
