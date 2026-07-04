"""
Setup script to verify the environment and dependencies for the project.
This script ensures that Python 3.11+ is used and that critical packages are installed.
"""
import sys
import importlib.metadata

MIN_PYTHON_VERSION = (3, 11)
REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "scipy",
    "scikit-learn",
    "biom-format",
    "skbio",
    "statsmodels",
    "requests",
    "tqdm",
    "loguru",
]

def check_python_version():
    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"ERROR: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python version check passed: {sys.version}")

def check_packages():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            version = importlib.metadata.version(pkg)
            print(f"✓ {pkg}=={version} installed")
        except importlib.metadata.PackageNotFoundError:
            missing.append(pkg)
    
    if missing:
        print(f"\nERROR: Missing required packages: {', '.join(missing)}")
        print("Please install them using: pip install -r code/requirements.txt")
        sys.exit(1)
    print("\n✓ All required packages are installed.")

if __name__ == "__main__":
    check_python_version()
    check_packages()