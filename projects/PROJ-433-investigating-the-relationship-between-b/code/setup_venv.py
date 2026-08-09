"""
Script to create a Python virtual environment for the project.

This script creates a virtual environment in the repository root named 'venv'
using Python 3.11. It verifies the Python version and handles the creation
process, exiting with a clear error message if the required Python version
is not available.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """Create the virtual environment in the repository root."""
    # Determine the repository root (assuming this script is in code/)
    repo_root = Path(__file__).resolve().parent.parent
    venv_path = repo_root / "venv"

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"Error: Python 3.11 or higher is required. "
              f"Current version: {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)

    # Check if venv already exists
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        print("To recreate, manually delete the 'venv' directory first.")
        return 0

    print(f"Creating virtual environment at {venv_path} using Python {sys.executable}...")
    
    try:
        # Create the virtual environment
        # Using subprocess to ensure we get the correct exit code handling
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        print("Virtual environment created successfully.")
        
        # Verify creation by checking for key files
        if (venv_path / "pyvenv.cfg").exists():
            print("Verification: pyvenv.cfg found.")
        else:
            print("Warning: pyvenv.cfg not found after creation.")
            
        # Check for activation script based on OS
        if os.name == "nt":
            activate_script = venv_path / "Scripts" / "activate.bat"
        else:
            activate_script = venv_path / "bin" / "activate"
            
        if activate_script.exists():
            print(f"Verification: Activation script found at {activate_script}.")
            print(f"To activate, run: source {activate_script} (Linux/Mac) or {activate_script} (Windows)")
        else:
            print(f"Warning: Activation script not found at {activate_script}.")
            
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Error: Python executable not found at {sys.executable}")
        return 1

if __name__ == "__main__":
    sys.exit(main())