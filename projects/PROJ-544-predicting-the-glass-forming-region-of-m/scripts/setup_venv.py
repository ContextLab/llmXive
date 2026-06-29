#!/usr/bin/env python3
"""
Python-based venv setup script for PROJ-544.

This script initializes a Python virtual environment and installs
dependencies from requirements.txt.

Usage:
    python scripts/setup_venv.py
"""

import subprocess
import sys
import os
from pathlib import Path

VENV_DIR = ".venv"
REQUIREMENTS_FILE = "requirements.txt"

def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check)
    return result

def main() -> int:
    """Main setup routine."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("=== Setting up Python 3.11 virtual environment ===")

    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"Detected Python version: {python_version}")

    if not (python_version.startswith("3.1") or python_version.startswith("3.11")):
        print(f"WARNING: Python 3.11+ recommended. Current version: {python_version}")

    # Check if requirements.txt exists
    if not Path(REQUIREMENTS_FILE).exists():
        print(f"ERROR: {REQUIREMENTS_FILE} not found in project root!")
        return 1

    # Remove existing venv if present
    if Path(VENV_DIR).exists():
        print("Removing existing virtual environment...")
        import shutil
        shutil.rmtree(VENV_DIR)

    # Create virtual environment
    print(f"Creating virtual environment in {VENV_DIR}...")
    run_command([sys.executable, "-m", "venv", VENV_DIR])

    # Determine activate script based on platform
    if sys.platform == "win32":
        pip_path = Path(VENV_DIR) / "Scripts" / "pip.exe"
    else:
        pip_path = Path(VENV_DIR) / "bin" / "pip"

    # Upgrade pip
    print("Upgrading pip...")
    run_command([str(pip_path), "install", "--upgrade", "pip", "setuptools", "wheel"])

    # Install dependencies
    print(f"Installing dependencies from {REQUIREMENTS_FILE}...")
    run_command([str(pip_path), "install", "-r", REQUIREMENTS_FILE])

    print()
    print("=== Virtual environment setup complete ===")
    if sys.platform == "win32":
        print(f"To activate, run: .\\{VENV_DIR}\\Scripts\\activate")
    else:
        print(f"To activate, run: source {VENV_DIR}/bin/activate")
    print("To deactivate, run: deactivate")

    return 0

if __name__ == "__main__":
    sys.exit(main())