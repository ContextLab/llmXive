"""
Environment setup script for PROJ-002.
Validates Python version and installs dependencies from requirements.txt.
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Ensure Python 3.11+ is being used."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"Error: Python 3.11+ is required. Found {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✓ Python version check passed: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    project_root = Path(__file__).parent
    req_file = project_root / "requirements.txt"
    
    if not req_file.exists():
        print(f"Error: {req_file} not found.")
        sys.exit(1)

    print("Installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(req_file), "--upgrade"
        ])
        print("✓ Python dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to install dependencies: {e}")
        sys.exit(1)

def main():
    """Main entry point for environment setup."""
    print("=== PROJ-002 Environment Setup ===")
    check_python_version()
    install_dependencies()
    print("=== Setup Complete ===")

if __name__ == "__main__":
    main()
