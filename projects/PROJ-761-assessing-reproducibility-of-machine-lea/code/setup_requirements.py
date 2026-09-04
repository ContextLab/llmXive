"""
Script to verify and document the installation requirements for the project.
This script ensures that the requirements.txt file is correctly formatted
and provides instructions for installing dependencies with the correct index URL.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Verifies the existence of requirements.txt and prints installation instructions.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        print("ERROR: requirements.txt not found at the project root.")
        sys.exit(1)

    print("Found requirements.txt.")
    print("\nInstallation Instructions:")
    print("-" * 40)
    print("To install dependencies, run the following command:")
    print(f"pip install -r {requirements_path} --extra-index-url https://download.pytorch.org/whl/cpu")
    print("-" * 40)
    
    # Verify content
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    required_packages = [
        "torch==2.2.0+cpu",
        "scikit-learn==1.5.0",
        "rdkit==2024.3.1",
        "statsmodels==0.14.1",
        "pandas==2.2.0",
        "numpy==1.26.0",
        "matplotlib==3.8.0",
        "pyyaml==6.0.1",
        "requests==2.31.0"
    ]

    missing = []
    for pkg in required_packages:
        if pkg not in content:
            missing.append(pkg)

    if missing:
        print(f"\nWARNING: The following packages are missing or have incorrect versions in requirements.txt:")
        for pkg in missing:
            print(f"  - {pkg}")
        sys.exit(1)
    
    print("\nAll required packages are present with correct versions.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
