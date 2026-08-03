import subprocess
import sys
import os
import venv
from pathlib import Path

def ensure_virtual_environment(venv_path: Path) -> bool:
    """
    Creates a virtual environment if it doesn't exist.
    Returns True if the venv is ready (created or already existing).
    """
    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path}...")
        try:
            venv.create(venv_path, with_pip=True)
            print(f"Virtual environment created successfully.")
            return True
        except Exception as e:
            print(f"Failed to create virtual environment: {e}")
            return False
    else:
        print(f"Virtual environment already exists at {venv_path}.")
        return True

def install_dependencies(venv_path: Path, requirements_path: Path) -> bool:
    """
    Installs dependencies from requirements.txt into the virtual environment.
    Returns True if installation was successful.
    """
    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        return False

    # Determine the path to the pip executable within the venv
    if os.name == 'nt':  # Windows
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:  # Unix/Linux/macOS
        pip_exe = venv_path / "bin" / "pip"

    if not pip_exe.exists():
        print(f"Error: pip executable not found at {pip_exe}. Venv might be corrupted.")
        return False

    print(f"Installing dependencies from {requirements_path}...")
    try:
        # Run pip install with upgrade pip first to ensure compatibility
        subprocess.run([str(pip_exe), "install", "--upgrade", "pip"], check=True)
        # Install requirements
        subprocess.run([str(pip_exe), "install", "-r", str(requirements_path)], check=True)
        print("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during installation: {e}")
        return False

def main():
    """
    Main entry point for T002b: Install dependencies from requirements.txt in a virtual environment.
    Assumes requirements.txt is in the project root.
    """
    # Project root is typically the parent of 'code' if running from 'code', or current dir
    # Based on task description, we look for requirements.txt in the project root.
    # Let's assume the script is run from the project root or 'code' directory.
    # We'll look for requirements.txt in the current working directory first, then parent.
    current_dir = Path.cwd()
    requirements_candidates = [
        current_dir / "requirements.txt",
        current_dir.parent / "requirements.txt"
    ]

    requirements_path = None
    for candidate in requirements_candidates:
        if candidate.exists():
            requirements_path = candidate
            break

    if not requirements_path:
        print("Error: requirements.txt not found in current or parent directory.")
        sys.exit(1)

    print(f"Found requirements.txt at: {requirements_path}")

    # Define venv path. Usually 'venv' or '.venv' in project root.
    # Let's use 'venv' in the same directory as requirements.txt
    project_root = requirements_path.parent
    venv_path = project_root / "venv"

    # Ensure venv exists
    if not ensure_virtual_environment(venv_path):
        print("Failed to ensure virtual environment exists.")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies(venv_path, requirements_path):
        print("Failed to install dependencies.")
        sys.exit(1)

    print("Task T002b completed successfully.")

if __name__ == "__main__":
    main()
