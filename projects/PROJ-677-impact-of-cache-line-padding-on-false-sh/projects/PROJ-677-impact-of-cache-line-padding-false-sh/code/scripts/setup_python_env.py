#!/usr/bin/env python3
"""
Setup script for Python 3.11 environment with required dependencies.
Reads requirements.txt and installs dependencies.
"""
import subprocess
import sys
import os
from pathlib import Path

def get_project_root():
    """Find project root by looking for the specific project directory."""
    current = Path(__file__).resolve()
    # Navigate up to find the project root
    while current != current.parent:
        if (current / "projects" / "PROJ-677-impact-of-cache-line-padding-false-sh").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")

def main():
    project_root = get_project_root()
    requirements_file = project_root / "code" / "analysis" / "requirements.txt"

    if not requirements_file.exists():
        print(f"ERROR: requirements.txt not found at {requirements_file}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_file}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
            capture_output=False
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()