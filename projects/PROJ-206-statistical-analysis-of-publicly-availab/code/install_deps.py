import subprocess
import sys
import os
import venv
from pathlib import Path

def main():
    """
    Creates a virtual environment in the project root (if it doesn't exist)
    and installs dependencies from requirements.txt.
    """
    project_root = Path(__file__).resolve().parent.parent
    venv_path = project_root / "venv"
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: {requirements_path} not found.")
        sys.exit(1)

    # Create virtual environment if it doesn't exist
    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path}...")
        venv.create(venv_path, with_pip=True)
    else:
        print(f"Virtual environment already exists at {venv_path}.")

    # Determine the correct pip path based on OS
    if os.name == 'nt':
        pip_path = venv_path / "Scripts" / "pip"
    else:
        pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print(f"Error: pip not found at {pip_path}. Virtual environment may be corrupted.")
        sys.exit(1)

    # Upgrade pip first
    print("Upgrading pip...")
    subprocess.check_call([str(pip_path), "install", "--upgrade", "pip"])

    # Install dependencies
    print(f"Installing dependencies from {requirements_path}...")
    subprocess.check_call([str(pip_path), "install", "-r", str(requirements_path)])

    print("Dependencies installed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
