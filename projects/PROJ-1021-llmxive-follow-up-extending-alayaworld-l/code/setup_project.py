"""
T002: Initialize Python 3.11 project structure and verify dependencies.

This script ensures the project root is set up correctly for the llmXive
AlayaWorld extension. It validates the existence of the code directory
and prepares the environment for dependency installation.

Usage:
    python code/setup_project.py
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Determine project root (parent of code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    code_dir = project_root / "code"
    
    print(f"Project Root: {project_root}")
    print(f"Code Directory: {code_dir}")
    
    # Verify code directory exists (created by T001a)
    if not code_dir.exists():
        print(f"ERROR: Code directory {code_dir} does not exist. Run T001a first.")
        sys.exit(1)
    
    # Verify Python version
    if sys.version_info < (3, 11):
        print(f"WARNING: Python version {sys.version_info.major}.{sys.version_info.minor} detected. "
              f"Project requires Python 3.11+ for optimal compatibility with torch/bitsandbytes.")
    
    # Check requirements.txt exists
    req_file = code_dir / "requirements.txt"
    if not req_file.exists():
        print(f"ERROR: requirements.txt not found at {req_file}.")
        sys.exit(1)
    
    print("Project structure validated.")
    print(f"Dependencies listed in {req_file}:")
    with open(req_file, "r") as f:
        deps = f.read().strip().splitlines()
        for dep in deps:
            print(f"  - {dep}")
    
    # Attempt to verify key dependencies are importable (soft check)
    # Note: We do not force install here to avoid network issues in the runner,
    # but we check if the environment is ready.
    missing = []
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python-headless")
    
    if missing:
        print(f"\nWARNING: The following dependencies are missing: {missing}")
        print("Please run: pip install -r code/requirements.txt")
        print("The project is initialized, but execution will fail until dependencies are installed.")
    else:
        print("\nCore dependencies detected in environment.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())