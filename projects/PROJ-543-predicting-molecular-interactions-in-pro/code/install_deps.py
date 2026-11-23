"""
Dependency installation script for PROJ-543.
Reads requirements.txt and installs packages into the active virtual environment.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Ensure pip is up to date
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ])
        
        print("All dependencies installed successfully.")
        
        # Verify key packages
        import torch
        import rdkit
        import datasets
        import sklearn
        import pandas
        import yaml
        from Bio import Align
        
        print("Verification successful: All core packages are importable.")
        
    except subprocess.CalledProcessError as e:
        print(f"Installation failed with error code: {e.returncode}")
        sys.exit(1)
    except ImportError as e:
        print(f"Verification failed: Could not import a required package: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
