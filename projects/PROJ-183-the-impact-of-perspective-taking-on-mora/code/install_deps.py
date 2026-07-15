import subprocess
import sys
import os

def main():
    """
    Installs dependencies from requirements.txt and verifies imports.
    This script implements Task T003: Install dependencies and verify imports.
    """
    print("Installing dependencies from requirements.txt...")
    
    # Install packages
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print("ERROR: Failed to install dependencies.")
        sys.exit(1)
    
    print("\nDependencies installed successfully.")
    print("Verifying imports in a fresh shell...")
    
    # List of packages to verify
    packages = [
        "pandas",
        "scipy",
        "statsmodels",
        "numpy",
        "requests",
        "yaml",  # pyyaml exposes 'yaml'
        "jsonschema",
        "vaderSentiment"
    ]
    
    failed_imports = []
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"  ✓ {pkg}")
        except ImportError as e:
            print(f"  ✗ {pkg}: {e}")
            failed_imports.append(pkg)
    
    if failed_imports:
        print(f"\nERROR: The following imports failed: {', '.join(failed_imports)}")
        sys.exit(1)
    
    print("\nAll dependencies installed and verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
