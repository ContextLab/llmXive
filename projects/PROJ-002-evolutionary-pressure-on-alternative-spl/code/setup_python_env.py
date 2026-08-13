"""
Setup script to verify Python environment and install dependencies.
This script ensures the required Python version and installs dependencies
from requirements.txt.
"""
import sys
import subprocess
import os
from pathlib import Path

REQUIRED_PYTHON_MAJOR = 3
REQUIRED_PYTHON_MINOR = 11

def check_python_version():
    """Verify the running Python version matches requirements."""
    current_major = sys.version_info.major
    current_minor = sys.version_info.minor

    if current_major != REQUIRED_PYTHON_MAJOR or current_minor < REQUIRED_PYTHON_MINOR:
        print(f"ERROR: Python {REQUIRED_PYTHON_MAJOR}.{REQUIRED_PYTHON_MINOR}+ is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✓ Python version check passed: {sys.version_info.major}.{sys.version_info.minor}")

def install_dependencies():
    """Install dependencies from requirements.txt."""
    req_file = Path(__file__).parent.parent / "requirements.txt"
    
    if not req_file.exists():
        print(f"ERROR: requirements.txt not found at {req_file}")
        sys.exit(1)

    print(f"Installing dependencies from {req_file}...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(req_file), "--upgrade"
        ])
        print("✓ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def main():
    print("=== PROJ-002 Environment Setup ===")
    check_python_version()
    install_dependencies()
    print("=== Setup Complete ===")

if __name__ == "__main__":
    main()
