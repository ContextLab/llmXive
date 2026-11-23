"""
Task T037a: Install dependencies and set up virtual environment for validation run.

This script creates a virtual environment in the project root (if not exists),
upgrades pip, and installs all dependencies from code/requirements.txt.
It is designed to be run from the project root directory.
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a shell command and raise an error if it fails."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        capture_output=False,
        text=True
    )
    return result.returncode

def main():
    # Determine project root based on the known structure
    # We assume this script is run from the project root or we navigate to it
    current_dir = Path.cwd()
    
    # Check if we are in the project root or a subdirectory
    # The project root for this specific task is: projects/PROJ-298-statistical-analysis-of-publicly-availab/
    # However, the script itself is located at code/setup_env.py relative to that root.
    # We need to find the root where 'data', 'code', 'tests' exist.
    
    root_candidates = [current_dir, current_dir.parent]
    project_root = None
    
    for candidate in root_candidates:
        if (candidate / 'code').exists() and (candidate / 'data').exists() and (candidate / 'tests').exists():
            project_root = candidate
            break
    
    if not project_root:
        # Fallback: assume current directory is the root if it matches the expected name pattern
        if "PROJ-298" in str(current_dir):
            project_root = current_dir
        else:
            print("Error: Could not determine project root. Please run this script from the project root directory.")
            sys.exit(1)

    print(f"Project root detected at: {project_root}")

    venv_path = project_root / ".venv"
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    # 1. Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path}...")
        venv.create(venv_path, with_pip=True)
        print("Virtual environment created.")
    else:
        print(f"Virtual environment already exists at {venv_path}.")

    # 2. Determine the python executable path
    if sys.platform == "win32":
        python_executable = venv_path / "Scripts" / "python.exe"
        pip_executable = venv_path / "Scripts" / "pip.exe"
    else:
        python_executable = venv_path / "bin" / "python"
        pip_executable = venv_path / "bin" / "pip"

    if not python_executable.exists():
        print(f"Error: Python executable not found at {python_executable}")
        sys.exit(1)

    # 3. Upgrade pip
    print("Upgrading pip...")
    retcode = run_command([str(python_executable), "-m", "pip", "install", "--upgrade", "pip"])
    if retcode != 0:
        print("Warning: Failed to upgrade pip, but continuing...")

    # 4. Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    retcode = run_command([
        str(python_executable), "-m", "pip", "install", "-r", str(requirements_path)
    ])

    if retcode != 0:
        print("Error: Failed to install dependencies. Please check the output above.")
        sys.exit(1)

    print("Dependencies installed successfully.")
    print(f"You can now activate the environment using: source {venv_path}/bin/activate (Linux/Mac) or {venv_path}\\Scripts\\activate (Windows)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())