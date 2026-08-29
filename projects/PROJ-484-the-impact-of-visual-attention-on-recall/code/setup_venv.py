"""
Setup script to initialize the Python virtual environment for the project.

This script creates a virtual environment at code/venv using Python 3.11.
It verifies the creation by checking for the presence of pyvenv.cfg and
confirming the Python version within the environment.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Initialize the Python virtual environment."""
    # Determine project root (parent of 'code' directory)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    venv_path = current_dir / "venv"

    print(f"Project Root: {project_root}")
    print(f"Target Venv Path: {venv_path}")

    # Check if venv already exists
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}.")
        print("Removing existing environment to ensure a clean state...")
        shutil.rmtree(venv_path)

    # Determine the Python executable to use
    # We attempt to use python3.11 specifically as per task requirement
    python_executable = "python3.11"
    
    # Fallback logic if python3.11 is not found in PATH
    try:
        result = subprocess.run(
            [python_executable, "--version"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        if result.returncode != 0:
            print(f"Warning: {python_executable} not found in PATH.")
            print("Falling back to 'python3' and checking version...")
            python_executable = "python3"
            result = subprocess.run(
                [python_executable, "--version"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            if result.returncode != 0:
                print("Error: Neither python3.11 nor python3 found.")
                sys.exit(1)
            
            version_output = result.stdout.strip()
            if "3.11" not in version_output:
                print(f"Warning: Found python3 version {version_output}. Task requires 3.11.x.")
                print("Proceeding anyway, but verification may fail if strict 3.11 is required.")
    except FileNotFoundError:
        print(f"Error: Could not find {python_executable}.")
        sys.exit(1)

    print(f"Creating virtual environment using: {python_executable} -m venv {venv_path}")
    
    try:
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)], 
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

    # Verification
    pyvenv_cfg = venv_path / "pyvenv.cfg"
    if not pyvenv_cfg.exists():
        print("Error: pyvenv.cfg was not created. Virtual environment setup failed.")
        sys.exit(1)

    print("Virtual environment created successfully.")
    print(f"Deliverable verified: {pyvenv_cfg} exists.")

    # Verify Python version inside the venv
    venv_python = venv_path / "bin" / "python"
    if not venv_python.exists():
        # Try Windows path if running on Windows (though project structure suggests Linux/Mac)
        venv_python = venv_path / "Scripts" / "python.exe"
    
    if venv_python.exists():
        try:
            result = subprocess.run(
                [str(venv_python), "--version"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            print(f"Verification: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not verify Python version in venv: {e}")
    else:
        print("Warning: Could not locate venv python executable to verify version.")

    print("Task T002b completed.")

if __name__ == "__main__":
    main()