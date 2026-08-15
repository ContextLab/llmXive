"""
Environment Setup Script for PROJ-002
Verifies Python 3.11+ and installs required dependencies.
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Ensure Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"ERROR: Python 3.11+ is required. Found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"Python version check passed: {version.major}.{version.minor}.{version.micro}")

def install_dependencies():
    """Install dependencies from requirements.txt."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)
    
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "--upgrade"
        ])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def main():
    """Main entry point for environment setup."""
    check_python_version()
    install_dependencies()
    print("Environment setup complete.")

if __name__ == "__main__":
    main()
