import os
import sys
import subprocess
import venv
from pathlib import Path

def main():
    """
    Creates a Python 3.11 virtual environment in the project root.
    Also generates an activation script and prints instructions.
    """
    project_root = Path(__file__).resolve().parent
    venv_path = project_root / "venv"

    print(f"Setting up Python virtual environment at: {venv_path}")

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"Error: This script requires Python 3.11 or higher. Current version: {sys.version}")
        sys.exit(1)

    # Create the virtual environment
    try:
        venv.create(venv_path, with_pip=True)
        print("Virtual environment created successfully.")
    except FileExistsError:
        print("Virtual environment already exists. Skipping creation.")
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

    # Generate activation script path
    if os.name == 'nt':
        activate_script = venv_path / "Scripts" / "activate.bat"
        activate_ps = venv_path / "Scripts" / "Activate.ps1"
    else:
        activate_script = venv_path / "bin" / "activate"
        activate_ps = None

    if activate_script.exists():
        print(f"\nActivation script created at: {activate_script}")
        print("To activate the environment, run:")
        if os.name == 'nt':
            print(f"  {activate_script}")
        else:
            print(f"  source {activate_script}")
        
        if activate_ps and os.name == 'nt':
            print(f"\nOr for PowerShell:")
            print(f"  & {activate_ps}")
    else:
        print("Warning: Activation script not found after creation.")
        sys.exit(1)

    print("\nNext step: Activate the environment and install dependencies from requirements.txt")

if __name__ == "__main__":
    main()
