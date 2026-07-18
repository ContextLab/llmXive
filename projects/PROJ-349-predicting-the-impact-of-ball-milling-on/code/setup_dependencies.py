"""
Script to verify and install project dependencies.
This script reads requirements.txt and ensures all packages are installed.
It also performs a basic import check to validate the environment.
"""
import subprocess
import sys
import importlib
from pathlib import Path

REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "scikit-learn",
    "statsmodels",
    "matplotlib",
    "seaborn",
    "requests",
    "tqdm",
    "pyarrow",
    "pdfminer.six",
]

def check_installation():
    """Check if all required packages are installed."""
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            # Map package name to import name if they differ
            if package == "pdfminer.six":
                import_name = "pdfminer"
            else:
                import_name = package.replace("-", "_")
            
            importlib.import_module(import_name)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing")
            missing.append(package)
    
    return missing

def install_dependencies():
    """Install dependencies from requirements.txt."""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("Error: requirements.txt not found in project root.")
        sys.exit(1)
    
    print(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def main():
    print("Checking project dependencies...")
    missing = check_installation()
    
    if missing:
        print("\nThe following packages are missing:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nAttempting to install missing packages...")
        install_dependencies()
    else:
        print("\nAll required dependencies are installed.")
        
    # Final verification
    print("\nFinal verification:")
    final_missing = check_installation()
    if final_missing:
        print("Warning: Some packages could not be installed or imported.")
        sys.exit(1)
    else:
        print("Environment ready for Python 3.11 project.")

if __name__ == "__main__":
    main()