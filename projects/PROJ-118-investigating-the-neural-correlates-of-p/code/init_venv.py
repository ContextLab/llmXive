"""
Script to initialize the Python 3.11 virtual environment.
This script ensures the 'venv' directory exists in the project root.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return

    print(f"Creating Python virtual environment at {venv_path}...")
    try:
        # Use the current Python interpreter to create the venv
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("Virtual environment created successfully.")
        
        # Verify the python executable exists
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        if python_exe.exists():
            print(f"Verified python executable at: {python_exe}")
        else:
            print("Warning: Python executable not found in expected location.")
            
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e.stderr.decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()