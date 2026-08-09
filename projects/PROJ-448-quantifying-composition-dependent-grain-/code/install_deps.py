"""
Script to install project dependencies from requirements.txt.

This script executes the installation of all dependencies defined in
projects/PROJ-448-quantifying-grain-boundary-segregation/requirements.txt.
It is designed to be run from the project root or the specific project directory.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # Determine the path to requirements.txt
    # The task context specifies the project root is projects/PROJ-448-...
    # We look for requirements.txt relative to the script's location or project root.
    # Assuming this script is run from the project root or the project directory.
    
    # Try to locate requirements.txt in the current working directory first
    req_path = Path("requirements.txt")
    
    if not req_path.exists():
        # Check if we are in the project root and it's in the parent or specific folder
        # Based on T001a/T001b, the project root is `projects/PROJ-448-quantifying-grain-boundary-segregation/`
        # If run from there, it should be right there.
        # If run from repo root, it might be `projects/PROJ-448-quantifying-grain-boundary-segregation/requirements.txt`
        project_dir = Path("projects/PROJ-448-quantifying-grain-boundary-segregation")
        if project_dir.exists():
            req_path = project_dir / "requirements.txt"
        else:
            print("Error: requirements.txt not found in current directory or expected project path.")
            sys.exit(1)

    if not req_path.exists():
        print(f"Error: Could not find {req_path}")
        sys.exit(1)

    print(f"Installing dependencies from: {req_path}")
    
    try:
        # Run pip install with the requirements file
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_path)],
            check=True,
            capture_output=False,
            text=True
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()