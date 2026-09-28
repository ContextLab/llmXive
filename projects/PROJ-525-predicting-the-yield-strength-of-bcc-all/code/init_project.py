"""
Initialization script for T002: Python 3.11 Project Setup.

This script validates the project structure and dependencies.
It is intended to be run after `pip install -r requirements.txt`.
"""
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Ensure Python 3.11 is being used."""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        print(f"ERROR: Python 3.11 is required. Found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python version check passed: {version.major}.{version.minor}.{version.micro}")

def check_dependencies():
    """Verify required packages are installed and importable."""
    required = [
        "numpy", "pandas", "scipy", "scikit-learn", 
        "periodictable", "pymatgen", "skbio", "requests"
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✓ {pkg} imported successfully")
        except ImportError:
            missing.append(pkg)
            print(f"✗ {pkg} NOT found")
    
    if missing:
        print(f"\nERROR: Missing dependencies: {missing}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    print("✓ All core dependencies verified")

def check_dev_tools():
    """Verify dev tools (ruff, black, pytest) are available."""
    tools = ["ruff", "black", "pytest"]
    missing = []
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], capture_output=True, check=True)
            print(f"✓ {tool} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
            print(f"✗ {tool} not found")
    
    if missing:
        print(f"\nWARNING: Dev tools missing: {missing}")
        print("Run: pip install -r requirements.txt (dev extras)")
    else:
        print("✓ Dev tools verified")

def main():
    print("Initializing PROJ-525 Project Environment...")
    print("-" * 40)
    
    check_python_version()
    check_dependencies()
    check_dev_tools()
    
    print("-" * 40)
    print("Project initialization complete.")
    print("Next steps: Run 'python code/01_download.py' to fetch data.")

if __name__ == "__main__":
    main()