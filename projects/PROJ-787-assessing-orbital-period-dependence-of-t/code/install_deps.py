"""
Script to install dependencies from code/requirements.txt into the current environment.

This script ensures that all packages listed in requirements.txt are installed.
It uses pip directly to handle the installation process.

Usage:
    python code/install_deps.py
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Determine the path to requirements.txt relative to this script
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Run pip install with the requirements file
        # Using sys.executable ensures we use the correct Python interpreter
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=False,
            text=True
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()