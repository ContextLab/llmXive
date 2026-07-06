"""
Task T005: Setup Python 3.11 virtualenv and install dependencies from requirements.txt.

This script:
1. Verifies Python 3.11 is available.
2. Creates a virtual environment at 'venv' in the project root.
3. Installs dependencies from 'requirements.txt'.
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def check_python_version():
    """Ensure Python 3.11 is being used or available."""
    # Check current interpreter
    current_version = sys.version_info
    if current_version.major == 3 and current_version.minor == 11:
        print(f"Using Python 3.11.{current_version.micro}")
        return True, None
    
    # If not 3.11, check if python3.11 command exists
    try:
        result = subprocess.run(
            ["python3.11", "--version"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"Found python3.11: {result.stdout.strip()}")
        return True, "python3.11"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "Python 3.11 not found in PATH"

def create_venv(venv_path: Path, python_exe: str = None):
    """Create virtual environment."""
    cmd = [sys.executable, "-m", "venv", str(venv_path)]
    if python_exe:
        # If we found python3.11 but aren't running it, use it
        cmd = [python_exe, "-m", "venv", str(venv_path)]
    
    print(f"Creating virtual environment at {venv_path}...")
    try:
        subprocess.run(cmd, check=True)
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create virtual environment: {e}")

def activate_and_install(venv_path: Path, requirements_path: Path):
    """Activate venv and install requirements."""
    if not requirements_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {requirements_path}")

    # Determine pip path based on OS
    if os.name == "nt":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"

    if not pip_path.exists():
        raise FileNotFoundError(f"pip not found in venv at {pip_path}")

    print(f"Installing dependencies from {requirements_path}...")
    try:
        # Upgrade pip first
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([str(pip_path), "install", "-r", str(requirements_path)], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to install dependencies: {e}")

def main():
    """Main entry point for T005."""
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    print("Starting T005: Setup Python 3.11 virtualenv and install dependencies...")

    # Step 1: Check Python version
    has_311, python_exe = check_python_version()
    if not has_311:
        print(f"ERROR: {python_exe}")
        sys.exit(1)

    # Step 2: Remove existing venv if present to ensure clean state
    if venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}...")
        shutil.rmtree(venv_path)

    # Step 3: Create venv
    create_venv(venv_path, python_exe)

    # Step 4: Install dependencies
    activate_and_install(venv_path, requirements_path)

    print("T005 completed successfully.")

if __name__ == "__main__":
    main()
