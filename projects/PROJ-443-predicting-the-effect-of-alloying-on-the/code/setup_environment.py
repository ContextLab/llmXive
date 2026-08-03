"""
Environment setup script to verify Python version and install dependencies.
This script ensures the project runs within the specified constraints (Python 3.11, CPU-only).
"""
import os
import subprocess
import sys
from pathlib import Path

REQUIRED_PYTHON_VERSION = (3, 11)
MAX_CORES = 2
MAX_RAM_GB = 7

def verify_python_version():
    """Verify that the running Python version matches the requirement."""
    current_version = sys.version_info[:2]
    if current_version != REQUIRED_PYTHON_VERSION:
        print(f"Error: Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]} is required.")
        print(f"Current version: {current_version[0]}.{current_version[1]}")
        sys.exit(1)
    print(f"Python version verified: {sys.version}")

def install_dependencies():
    """Install dependencies from requirements.txt if not already installed."""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("Error: requirements.txt not found.")
        sys.exit(1)

    print("Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
        ])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create the necessary project directory structure."""
    dirs = [
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/results",
        "code/figures",
        "code/specs"
    ]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def main():
    """Main entry point for environment setup."""
    print("Starting project environment setup...")
    verify_python_version()
    create_directories()
    install_dependencies()
    print("Environment setup complete.")
    print(f"Constraints: CPU-only (n_jobs={MAX_CORES}), RAM limit ~{MAX_RAM_GB}GB")

if __name__ == "__main__":
    main()