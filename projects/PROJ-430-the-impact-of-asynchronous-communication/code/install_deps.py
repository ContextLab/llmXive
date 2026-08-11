"""
Script to install dependencies from requirements.txt within the virtual environment.
This script is intended to be run after the virtual environment is activated.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Installs dependencies listed in requirements.txt.
    Exits with error code if installation fails.
    """
    # Determine the path to requirements.txt relative to the project root.
    # Assuming this script is in code/ and requirements.txt is in the project root.
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    # Use sys.executable to ensure we are installing into the current Python environment
    # (which should be the venv if activated).
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print("Dependencies installed successfully.")
        else:
            print("Installation failed with return code: {}".format(result.returncode), file=sys.stderr)
            sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: pip executable not found.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()