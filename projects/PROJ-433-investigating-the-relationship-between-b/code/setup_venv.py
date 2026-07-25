"""
Script to create a Python virtual environment for the project.
Task T002a: Create Python virtual environment.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Creates a virtual environment in the repository root using python3.11.
    """
    # Determine the project root (parent of the code/ directory where this script lives)
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent

    venv_path = project_root / "venv"

    if venv_path.exists():
        print(f"Virtual environment already exists at: {venv_path}")
        print("Skipping creation. To recreate, manually remove the 'venv' directory first.")
        return 0

    print(f"Creating virtual environment at: {venv_path}")
    
    # Check for python3.11 availability
    python_executable = "python3.11"
    try:
        result = subprocess.run(
            [python_executable, "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Using: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to generic python3 if 3.11 not explicitly found, 
        # though the task specifies python3.11
        print(f"Warning: {python_executable} not found. Attempting to use 'python3'.")
        python_executable = "python3"
        try:
            subprocess.run([python_executable, "--version"], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Error: Could not find python3 or python3.11.")
            return 1

    try:
        subprocess.run(
            [python_executable, "-m", "venv", str(venv_path)],
            check=True
        )
        print("Virtual environment created successfully.")
        print(f"Activate with: source {venv_path}/bin/activate")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())