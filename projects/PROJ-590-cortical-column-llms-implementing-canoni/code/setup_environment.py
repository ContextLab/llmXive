"""
Script to verify the Python environment and dependencies for T002.
This script ensures that the project structure is valid and dependencies
can be imported without error.
"""
import sys
import importlib

REQUIRED_PACKAGES = [
    "torch",
    "numpy",
    "scipy",
    "pytest",
    "psutil",
]

def check_import(package_name: str) -> bool:
    """Attempt to import a package and return success status."""
    try:
        importlib.import_module(package_name)
        print(f"  [OK] {package_name}")
        return True
    except ImportError as e:
        print(f"  [FAIL] {package_name}: {e}")
        return False

def main():
    print(f"Python version: {sys.version}")
    print(f"Checking required packages...")
    
    all_ok = True
    for pkg in REQUIRED_PACKAGES:
        if not check_import(pkg):
            all_ok = False

    if all_ok:
        print("\n[SUCCESS] All dependencies are available.")
        return 0
    else:
        print("\n[ERROR] Some dependencies are missing. Please install them via requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())