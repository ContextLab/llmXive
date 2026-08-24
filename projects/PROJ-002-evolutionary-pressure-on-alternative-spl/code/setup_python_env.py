"""
Setup script to initialize the Python environment for PROJ-002.
Creates virtualenv and installs dependencies from requirements.txt.
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Ensure Python version is >= 3.9 (recommended 3.11)"""
    if sys.version_info < (3, 9):
        print(f"Error: Python 3.9+ is required. Found {sys.version}")
        sys.exit(1)
    print(f"Python version: {sys.version}")

def install_dependencies():
    """Install Python dependencies from requirements.txt"""
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print(f"Error: {req_file} not found")
        sys.exit(1)
    
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(req_file),
            "--upgrade"
        ])
        print("Python dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    check_python_version()
    install_dependencies()
    print("Environment setup complete.")

if __name__ == "__main__":
    main()
