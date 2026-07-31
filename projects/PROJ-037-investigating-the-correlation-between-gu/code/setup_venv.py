"""
Virtual Environment Setup Script for PROJ-037.

This script creates a Python virtual environment in the project root
and installs all dependencies listed in requirements.txt.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

# Project root is assumed to be the directory containing this script's parent
# or explicitly defined relative to the project structure.
# Based on task T002b context, we operate within the project root.
PROJECT_ROOT = Path(__file__).parent.parent
VENV_DIR = PROJECT_ROOT / "venv"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.
    
    Args:
        cmd: List of command arguments.
        check: If True, raise CalledProcessError on non-zero exit.
    
    Returns:
        CompletedProcess instance.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Return code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise

def main():
    """
    Main entry point for virtual environment setup.
    
    1. Checks if a venv already exists. If so, prompts for removal or skipping.
    2. Creates a new virtual environment using `python -m venv venv`.
    3. Identifies the correct pip executable within the new venv.
    4. Installs dependencies from requirements.txt.
    """
    print(f"Project Root: {PROJECT_ROOT}")
    
    # Check if requirements.txt exists
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(
            f"requirements.txt not found at {REQUIREMENTS_FILE}. "
            "Please ensure T002a (requirements.txt creation) is completed first."
        )

    # Check if venv already exists
    if VENV_DIR.exists():
        print(f"Virtual environment already exists at {VENV_DIR}.")
        response = input("Do you want to remove it and recreate? (y/n): ").strip().lower()
        if response == 'y':
            print(f"Removing existing venv at {VENV_DIR}...")
            shutil.rmtree(VENV_DIR)
            print("Removed.")
        else:
            print("Skipping venv creation. Please manually upgrade packages if needed.")
            return

    # Create virtual environment
    print(f"Creating virtual environment at {VENV_DIR}...")
    run_command([sys.executable, "-m", "venv", str(VENV_DIR)])

    # Determine the pip path based on OS
    if sys.platform == "win32":
        pip_path = VENV_DIR / "Scripts" / "pip.exe"
        python_path = VENV_DIR / "Scripts" / "python.exe"
    else:
        pip_path = VENV_DIR / "bin" / "pip"
        python_path = VENV_DIR / "bin" / "python"

    if not pip_path.exists():
        raise RuntimeError(f"Pip executable not found at {pip_path}. "
                           "Virtual environment creation may have failed.")

    # Upgrade pip first
    print("Upgrading pip...")
    run_command([str(python_path), "-m", "pip", "install", "--upgrade", "pip"])

    # Install requirements
    print(f"Installing requirements from {REQUIREMENTS_FILE}...")
    run_command([
        str(pip_path),
        "install",
        "-r",
        str(REQUIREMENTS_FILE)
    ])

    print("\nVirtual environment setup complete.")
    print(f"Activate the environment before running scripts:")
    if sys.platform == "win32":
        print(f"  {VENV_DIR}\\Scripts\\activate")
    else:
        print(f"  source {VENV_DIR}/bin/activate")

if __name__ == "__main__":
    main()