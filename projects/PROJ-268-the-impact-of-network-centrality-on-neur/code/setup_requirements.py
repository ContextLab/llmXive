"""
Script to install project dependencies and verify installation.
This script corresponds to task T001c.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    try:
        # Use pip to install requirements
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Installation output:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors (non-fatal):")
            print(result.stderr)
        
        # Verify key packages are installed
        packages_to_check = [
            "nibabel", "numpy", "scipy", "pandas", "networkx", 
            "scikit-learn", "matplotlib", "seaborn", "datasets", 
            "nilearn", "brainsmash", "tqdm"
        ]
        
        print("\nVerifying package installations...")
        for package in packages_to_check:
            try:
                __import__(package)
                print(f"  [OK] {package}")
            except ImportError as e:
                print(f"  [FAIL] {package}: {e}")
                sys.exit(1)
        
        print("\nAll dependencies installed and verified successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies.")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()