"""
Environment verification script for PROJ-122.
Verifies Python version and installed dependencies.
"""
import sys
import subprocess
import importlib

REQUIRED_PYTHON_VERSION = (3, 11)

def check_python_version():
    """Ensure Python version is 3.11 or higher."""
    current_version = sys.version_info[:2]
    if current_version < REQUIRED_PYTHON_VERSION:
        print(f"ERROR: Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version check passed: {sys.version.split()[0]}")

def check_dependencies():
    """Verify all required packages in requirements.txt are installed."""
    try:
        with open("requirements.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print("ERROR: requirements.txt not found in code/ directory.")
        sys.exit(1)

    missing = []
    for line in lines:
        # Parse package name (ignore version specifiers for import check)
        pkg_name = line.split(">=")[0].split("<=")[0].split("==")[0].split("[")[0].strip()
        if not pkg_name:
            continue

        try:
            if pkg_name == "rdkit":
                # RDKit is usually imported as rdkit, but sometimes requires specific handling
                importlib.import_module("rdkit")
            else:
                importlib.import_module(pkg_name)
            print(f"✓ {pkg_name} installed")
        except ImportError:
            missing.append(pkg_name)

    if missing:
        print(f"\nERROR: Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    print("\n✓ All dependencies verified.")

def main():
    print("Verifying PROJ-122 Environment...")
    check_python_version()
    check_dependencies()
    print("\nEnvironment verification complete.")

if __name__ == "__main__":
    main()