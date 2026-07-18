"""
Environment setup and verification script.
Checks Python version and validates installed dependencies.
"""
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Ensure Python version is 3.11 or higher."""
    major, minor, _ = sys.version_info
    if major < 3 or (major == 3 and minor < 11):
        print(f"ERROR: Python 3.11+ is required. Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version check passed: {sys.version}")

def check_dependencies():
    """Verify that required packages from requirements.txt are installed."""
    required_packages = [
        "pandas",
        "numpy",
        "scipy",
        "statsmodels",
        "matplotlib",
        "seaborn",
        "yaml",  # pyyaml exposes 'yaml'
    ]
    
    missing = []
    for pkg in required_packages:
        try:
            if pkg == "yaml":
                __import__("yaml")
            else:
                __import__(pkg)
            print(f"✓ {pkg} installed")
        except ImportError:
            missing.append(pkg)
            print(f"✗ {pkg} NOT FOUND")

    if missing:
        print(f"\nERROR: Missing required packages: {', '.join(missing)}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    print("✓ All dependencies verified.")

def main():
    """Entry point for environment verification."""
    print("Running environment checks...")
    check_python_version()
    check_dependencies()
    print("Environment setup complete.")

if __name__ == "__main__":
    main()