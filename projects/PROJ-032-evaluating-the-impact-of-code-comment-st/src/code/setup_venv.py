"""
Script to initialize the Python 3.9+ project environment for PROJ-032.

This script:
1. Creates a virtual environment in 'venv'.
2. Installs runtime dependencies from requirements.txt.
3. Installs development dependencies from dev-requirements.txt.

Usage:
    python src/code/setup_venv.py
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and print output."""
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        if check:
            sys.exit(1)

def main():
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "src" / "code" / "requirements.txt"
    dev_requirements_path = project_root / "src" / "code" / "dev-requirements.txt"

    # 1. Create virtual environment
    print(f"Creating virtual environment at {venv_path}...")
    if venv_path.exists():
        print("Virtual environment already exists. Skipping creation.")
    else:
        run_command([sys.executable, "-m", "venv", str(venv_path)])

    # Determine the pip executable in the venv
    if os.name == 'nt':
        pip_executable = venv_path / "Scripts" / "pip"
        python_executable = venv_path / "Scripts" / "python"
    else:
        pip_executable = venv_path / "bin" / "pip"
        python_executable = venv_path / "bin" / "python"

    # 2. Install runtime dependencies
    if requirements_path.exists():
        print(f"Installing runtime dependencies from {requirements_path}...")
        run_command([str(pip_executable), "install", "-r", str(requirements_path)])
    else:
        print(f"Warning: {requirements_path} not found. Skipping runtime dependencies.")

    # 3. Install development dependencies
    if dev_requirements_path.exists():
        print(f"Installing development dependencies from {dev_requirements_path}...")
        run_command([str(pip_executable), "install", "-r", str(dev_requirements_path)])
    else:
        print(f"Warning: {dev_requirements_path} not found. Skipping development dependencies.")

    print("Project initialization complete.")

if __name__ == "__main__":
    main()