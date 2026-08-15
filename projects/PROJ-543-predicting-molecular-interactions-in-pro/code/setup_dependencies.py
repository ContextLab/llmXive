"""
Dependency installation script for PROJ-543.
Installs required packages into the active virtual environment.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Install dependencies from requirements.txt into the current environment."""
    # Ensure we are running in the project root or code/ directory context
    script_dir = Path(__file__).parent
    requirements_path = script_dir / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    # Upgrade pip first to ensure compatibility with torch wheels
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

    # Install requirements
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()