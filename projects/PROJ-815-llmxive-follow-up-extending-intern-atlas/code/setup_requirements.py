"""
Script to initialize the Python environment for the project.
This script verifies the existence of requirements.txt and provides
instructions for installation.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """
    Main entry point for setup_requirements.
    Checks for requirements.txt and attempts to install dependencies.
    """
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        print("Please ensure T002 has been completed successfully.")
        sys.exit(1)

    print(f"Found requirements.txt at: {requirements_path}")
    print("To install dependencies, run the following command:")
    print(f"  pip install -r {requirements_path}")
    print("\nOr run this script with the --install flag:")
    print(f"  python {requirements_path.parent / 'setup_requirements.py'} --install")

    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        print("\nInstalling dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
            print("\n✅ Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Failed to install dependencies: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()