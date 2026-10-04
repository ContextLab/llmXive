"""
Project Initialization Script for T002.
Verifies Python version and checks for required dependencies.
"""
import sys
import subprocess
import json
from pathlib import Path

REQUIRED_PACKAGES = [
    "numpy", "pandas", "scipy", "scikit-learn",
    "periodictable", "pymatgen", "skbio", "requests", "pyyaml"
]

def check_python_version():
    """Ensure Python 3.11+ is being used."""
    if sys.version_info < (3, 11):
        print(f"ERROR: Python 3.11+ is required. Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version check passed: {sys.version}")

def check_dependencies():
    """Verify all required packages are installed."""
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
            print(f"✓ {package} found")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} NOT found")

    if missing:
        print(f"\nERROR: Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    print("\n✓ All dependencies verified.")

def check_dev_tools():
    """Check for essential development tools (optional but recommended)."""
    tools = ["git", "python3"]
    for tool in tools:
        try:
            subprocess.run([tool, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"✓ {tool} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠ {tool} not found in PATH")

def main():
    print("=== Project Initialization Check (T002) ===")
    check_python_version()
    check_dependencies()
    check_dev_tools()
    print("=== Initialization Check Complete ===")

if __name__ == "__main__":
    main()
