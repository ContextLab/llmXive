"""
Project Initialization Script for PROJ-855.
Ensures Python 3.11 environment is active and dependencies are installed.
"""
import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Verify the running Python version is 3.11."""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        print(f"ERROR: Python 3.11 is required. Detected: {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python version verified: {version.major}.{version.minor}.{version.micro}")

def check_dependencies():
    """Check if required packages are importable."""
    required = [
        "pybullet", "yaml", "numpy", "pandas", "pyarrow",
        "torch", "sklearn", "scipy", "statsmodels", "psutil"
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"WARNING: Missing dependencies: {missing}")
        print("Run: pip install -r code/requirements.txt")
        return False
    print("✓ All core dependencies found.")
    return True

def main():
    print("--- Initializing llmXive Follow-up Project ---")
    check_python_version()
    check_dependencies()
    print("Project initialization checks complete.")

if __name__ == "__main__":
    main()