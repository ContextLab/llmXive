"""
Project Initialization Script for Python 3.11 Environment.
Implements T008: Initialize Python 3.11 project with claim c_9da78e09.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def check_python_version():
    """Verify that the running Python interpreter is 3.11."""
    major, minor = sys.version_info[:2]
    if major != 3 or minor != 11:
        print(f"ERROR: Python 3.11 is required. Found: {major}.{minor}")
        print("Please ensure you are running this script with Python 3.11.")
        sys.exit(1)
    print(f"✓ Python version verified: {sys.version}")

def create_virtual_environment(root_dir: Path):
    """Create a .venv directory if it does not exist."""
    venv_path = root_dir / ".venv"
    if venv_path.exists():
        print(f"✓ Virtual environment already exists at {venv_path}")
        return venv_path

    print(f"Creating virtual environment at {venv_path}...")
    venv.create(venv_path, with_pip=True)
    print("✓ Virtual environment created.")
    return venv_path

def install_dependencies(root_dir: Path, venv_path: Path):
    """Install requirements from requirements.txt into the virtual environment."""
    req_file = root_dir / "requirements.txt"
    if not req_file.exists():
        print("WARNING: requirements.txt not found. Skipping dependency installation.")
        return

    pip_path = venv_path / "bin" / "pip"
    if not pip_path.exists():
        # Fallback for Windows
        pip_path = venv_path / "Scripts" / "pip.exe"

    if not pip_path.exists():
        print("ERROR: Could not locate pip in the virtual environment.")
        sys.exit(1)

    print("Installing dependencies from requirements.txt...")
    try:
        subprocess.check_call([str(pip_path), "install", "-r", str(req_file)])
        print("✓ Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def main():
    """Main entry point for project initialization."""
    # Determine project root (parent of this script)
    root_dir = Path(__file__).parent.resolve()
    print(f"Project root: {root_dir}")

    # 1. Check Python version (Claim c_9da78e09)
    check_python_version()

    # 2. Create Virtual Environment
    venv_path = create_virtual_environment(root_dir)

    # 3. Install Dependencies
    install_dependencies(root_dir, venv_path)

    print("\n✓ Project initialization complete.")
    print(f"To activate the environment, run: source {venv_path / 'bin' / 'activate'}")

if __name__ == "__main__":
    main()