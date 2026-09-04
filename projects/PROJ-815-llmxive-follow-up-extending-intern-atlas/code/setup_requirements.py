"""
Verification script for T002: Initialize Python 3.11 project.

This script attempts to install dependencies from code/requirements.txt
and verifies the installation was successful by importing key modules.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    print(f"Installing dependencies from {requirements_path}...")
    
    try:
        # Run pip install
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print("Installation output:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install requirements. Exit code: {e.returncode}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

    print("\nVerifying key imports...")
    required_imports = [
        "pandas",
        "numpy",
        "sklearn",
        "networkx",
        "requests",
        "yaml",
        "seaborn",
        "matplotlib",
        "Levenshtein",
        "statsmodels"
    ]

    failed_imports = []
    for module in required_imports:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            failed_imports.append(module)

    if failed_imports:
        print(f"\nERROR: The following modules failed to import: {failed_imports}")
        sys.exit(1)

    print("\n✓ All dependencies installed and verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())