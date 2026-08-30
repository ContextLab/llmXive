"""
Task T005: Install dependencies from code/requirements.txt.

This script installs the required packages and verifies their presence.
It is designed to be run within the project's virtual environment.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    logger = logging.getLogger(__name__)
    logger.info(f"Installing dependencies from {requirements_path}")

    # Install dependencies
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=False
        )
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

    # Required packages to verify
    required_packages = [
        "pandas",
        "numpy",
        "statsmodels",
        "requests",
        "scikit-learn",
        "matplotlib",
        "seaborn",
        "pyyaml",
        "pytrends"
    ]

    print("\nVerifying installed packages...")
    all_present = True

    for package in required_packages:
        try:
            # Use pip list to verify presence
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                capture_output=True,
                text=True,
                check=True
            )
            if package.lower() in result.stdout.lower():
                print(f"✓ {package} is installed")
            else:
                print(f"✗ {package} is MISSING")
                all_present = False
        except subprocess.CalledProcessError as e:
            print(f"✗ Error checking {package}: {e}")
            all_present = False

    if not all_present:
        print("\nERROR: One or more required packages are missing.")
        sys.exit(1)

    print("\nAll dependencies installed and verified successfully.")
    sys.exit(0)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()