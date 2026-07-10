"""
Script to check Python version and install dependencies.
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version() -> bool:
    """Verify Python 3.11+ is installed."""
    if sys.version_info < (3, 11):
        print(f"Error: Python 3.11+ required. Current version: {sys.version}")
        return False
    print(f"Python version check passed: {sys.version}")
    return True

def install_dependencies() -> None:
    """Install dependencies from requirements.txt."""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("Error: requirements.txt not found.")
        return
    
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"], check=True)
    print("Dependencies installed successfully.")

def main() -> None:
    """Main entry point."""
    if not check_python_version():
        sys.exit(1)
    install_dependencies()

if __name__ == "__main__":
    main()