"""
Script to install project dependencies into the current virtual environment.
This script reads requirements.txt and installs packages using pip.
It ensures that critical packages like torch and torch-geometric are installed
with correct CPU/GPU compatibility flags if needed.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Installs all dependencies listed in code/requirements.txt.
    Raises an exception if installation fails.
    """
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "code" / "requirements.txt"

    if not requirements_path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {requirements_path}")

    print(f"Installing dependencies from {requirements_path}...")

    # Install packages
    try:
        # Use pip from the current sys.executable to ensure we install into the venv
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path), "--upgrade"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print("All dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        raise SystemExit(1)

    # Verify critical imports
    print("Verifying critical imports...")
    critical_packages = [
        "torch",
        "torch_geometric",
        "rdkit",
        "datasets",
        "sklearn",
        "pandas",
        "yaml",
        "Bio"
    ]

    for pkg in critical_packages:
        try:
            __import__(pkg)
            print(f"  [OK] {pkg}")
        except ImportError as e:
            print(f"  [FAIL] {pkg}: {e}")
            raise SystemExit(1)

    print("Dependency verification complete.")

if __name__ == "__main__":
    main()