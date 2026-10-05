"""
Script to install dependencies for Project PROJ-402.
Reads requirements from projects/PROJ-402-the-impact-of-interoceptive-awareness-on/code/requirements.txt
and installs them into the current environment (or creates a venv if requested).

This script satisfies Task T002b: Install dependencies.
It ensures the specific requirements file exists and installs the packages.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    # Define the path to the requirements file as per T002e specification
    # The task requires the file to be at: projects/PROJ-402-the-impact-of-interoceptive-awareness-on/code/requirements.txt
    project_root = Path(__file__).parent.parent
    req_file_path = project_root / "projects" / "PROJ-402-the-impact-of-interoceptive-awareness-on" / "code" / "requirements.txt"

    if not req_file_path.exists():
        print(f"CRITICAL ERROR: Requirements file not found at expected path: {req_file_path}")
        print("Please ensure T002e has completed successfully and the file exists.")
        sys.exit(1)

    print(f"Found requirements file at: {req_file_path}")
    
    # Check if we are in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print("Note: Not running inside a virtual environment. Installing to global environment.")
        print("It is recommended to create a venv first, but proceeding with installation.")
    
    # Install dependencies
    print("Installing dependencies...")
    try:
        # Use pip from the current python executable to ensure correct target
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file_path)],
            check=True,
            capture_output=False,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies. Exit code: {e.returncode}")
        sys.exit(1)
    
    print("Dependencies installed successfully.")
    
    # Verification step: Import key packages to ensure they are loadable
    print("Verifying package imports...")
    packages_to_check = [
        "pandas", "numpy", "sklearn", "hrv_analysis", 
        "pybids", "requests", "yaml", "jsonschema", 
        "statsmodels", "wfdb"
    ]
    
    failed_imports = []
    for pkg in packages_to_check:
        try:
            __import__(pkg)
            print(f"  [OK] {pkg}")
        except ImportError as e:
            print(f"  [FAIL] {pkg}: {e}")
            failed_imports.append(pkg)
    
    if failed_imports:
        print(f"CRITICAL ERROR: The following packages failed to import: {failed_imports}")
        sys.exit(1)
    
    print("All verifications passed. Environment ready.")
    return 0

if __name__ == "__main__":
    sys.exit(main())