"""
Script to verify the Python 3.11 virtual environment and dependencies are correctly installed.
Run this after executing code/setup_venv.sh to validate the setup.
"""

import sys
import importlib.util

REQUIRED_PACKAGES = [
    "mne",
    "sklearn",
    "numpy",
    "pandas",
    "lempel_ziv_complexity",
    "scipy",
    "yaml",  # for pyyaml
    "pytest"
]

def check_python_version():
    """Ensure Python 3.11 is being used."""
    if sys.version_info.major != 3 or sys.version_info.minor != 11:
        print(f"Error: Python 3.11 is required. Found Python {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"Python version check passed: {sys.version}")
    return True

def check_packages():
    """Ensure all required packages are importable."""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"  [FAIL] {pkg}")
    
    if missing:
        print(f"\nError: Missing packages: {', '.join(missing)}")
        return False
    return True

def main():
    print("=== Environment Verification ===")
    if not check_python_version():
        sys.exit(1)
    
    print("\nChecking required packages...")
    if not check_packages():
        sys.exit(1)
    
    print("\n=== All checks passed. Environment is ready. ===")

if __name__ == "__main__":
    main()