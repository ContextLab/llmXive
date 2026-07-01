"""
Project initialization script for Python 3.11 environment setup.
Implements T008: Initialize Python 3.11 project with virtual environment and dependencies.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

# Ensure we are running on Python 3.11
REQUIRED_PYTHON_VERSION = (3, 11)

def check_python_version():
    """Check if the current Python version meets requirements."""
    current_version = sys.version_info[:2]
    if current_version < REQUIRED_PYTHON_VERSION:
        print(f"ERROR: Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ is required.")
        print(f"       Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version check passed: {sys.version}")
    return True

def create_venv(venv_path="code/.venv"):
    """Create a virtual environment at the specified path."""
    venv_path = Path(venv_path)
    if venv_path.exists():
        print(f"⚠ Virtual environment already exists at {venv_path}. Skipping creation.")
        return venv_path

    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print("✓ Virtual environment created successfully.")
    return venv_path

def install_requirements(venv_path="code/.venv", requirements_file="requirements.txt"):
    """Install dependencies from requirements.txt into the virtual environment."""
    venv_path = Path(venv_path)
    requirements_file = Path(requirements_file)

    if not requirements_file.exists():
        print(f"⚠ requirements.txt not found at {requirements_file}. Skipping installation.")
        return True

    # Determine the pip path based on OS
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print(f"ERROR: pip not found at {pip_path}. Virtual environment may be corrupted.")
        return False

    print(f"Installing dependencies from {requirements_file}...")
    try:
        subprocess.check_call([str(pip_path), "install", "--upgrade", "pip"])
        subprocess.check_call([str(pip_path), "install", "-r", str(requirements_file)])
        print("✓ Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        return False

def verify_installation(venv_path="code/.venv"):
    """Verify that the virtual environment is active and pip is available."""
    venv_path = Path(venv_path)
    
    # Check if the venv structure exists
    if not (venv_path / "pyvenv.cfg").exists():
        print(f"ERROR: {venv_path} does not appear to be a valid virtual environment.")
        return False

    # Check pip
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print(f"ERROR: pip executable not found at {pip_path}")
        return False

    # Run pip list to verify it works
    try:
        result = subprocess.run([str(pip_path), "list"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Virtual environment verification passed.")
            return True
        else:
            print(f"ERROR: pip list failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("ERROR: pip list timed out.")
        return False

def main():
    """Main entry point for project setup."""
    print("=== llmXive Project Initialization (T008) ===")
    
    # 1. Check Python version
    if not check_python_version():
        sys.exit(1)

    # 2. Create virtual environment
    venv_path = create_venv()

    # 3. Install requirements
    if not install_requirements(venv_path):
        print("ERROR: Dependency installation failed. Please check requirements.txt.")
        sys.exit(1)

    # 4. Verify installation
    if not verify_installation(venv_path):
        print("ERROR: Virtual environment verification failed.")
        sys.exit(1)

    print("\n=== Setup Complete ===")
    print(f"Activate the environment with:")
    if sys.platform == "win32":
        print(f"  {venv_path}\\Scripts\\activate")
    else:
        print(f"  source {venv_path}/bin/activate")

if __name__ == "__main__":
    main()
