"""
Script to initialize a Python 3.11 virtual environment for the project.

This script creates a virtual environment at `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/venv/`
using the system's Python 3.11 interpreter. It ensures the `venv` module is available
and exits with a clear error if Python 3.11 is not found.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def find_python311():
    """
    Locate the Python 3.11 interpreter.
    Checks standard names: python3.11, python3, and specific OS paths.
    Returns the path string or None if not found.
    """
    candidates = [
        "python3.11",
        "python3",
        "/usr/bin/python3.11",
        "/usr/local/bin/python3.11",
        "/opt/homebrew/bin/python3.11",  # macOS
        "C:\\Python311\\python.exe",     # Windows
    ]
    
    for candidate in candidates:
        try:
            # Check if command exists and is version 3.11
            result = subprocess.run(
                [candidate, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0 and "3.11" in result.stdout:
                return candidate
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    return None

def main():
    project_root = Path("projects/PROJ-884-llmxive-follow-up-extending-self-improvi")
    venv_path = project_root / "venv"

    if not project_root.exists():
        print(f"ERROR: Project root not found at {project_root}")
        print("Please run T001a (setup_structure) first to create the directory.")
        sys.exit(1)

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping initialization.")
        sys.exit(0)

    python_cmd = find_python311()
    if not python_cmd:
        print("ERROR: Python 3.11 interpreter not found.")
        print("Please ensure Python 3.11 is installed and available in your PATH as 'python3.11' or 'python3'.")
        sys.exit(1)

    print(f"Using Python interpreter: {python_cmd}")
    print(f"Creating virtual environment at: {venv_path}")

    try:
        # Create the virtual environment
        subprocess.run(
            [python_cmd, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Verify creation by checking for the activation script
        if sys.platform == "win32":
            activate_script = venv_path / "Scripts" / "activate.bat"
        else:
            activate_script = venv_path / "bin" / "activate"

        if not activate_script.exists():
            print(f"ERROR: Virtual environment creation appeared successful, but {activate_script} is missing.")
            sys.exit(1)

        print(f"SUCCESS: Virtual environment initialized at {venv_path}")
        print(f"Activate with: source {venv_path}/bin/activate  (Unix/Mac)")
        print(f"             : {venv_path}\\Scripts\\activate.bat  (Windows)")
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create virtual environment.")
        print(f"Stderr: {e.stderr.decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during venv creation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
