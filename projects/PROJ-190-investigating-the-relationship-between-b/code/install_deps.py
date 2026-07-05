"""
Script to install dependencies from requirements.txt.
This script ensures the environment is set up with pinned versions.
"""
import subprocess
import sys
import os
from pathlib import Path

def install_dependencies():
    """
    Installs all packages listed in requirements.txt using pip.
    """
    root = Path(__file__).resolve().parent.parent
    req_file = root / "requirements.txt"

    if not req_file.exists():
        print(f"Error: {req_file} not found.")
        sys.exit(1)

    print(f"Installing dependencies from {req_file}...")
    
    try:
        # Use subprocess to run pip install
        # -q: quiet output (optional, can remove for full verbosity)
        # --upgrade: ensure we get the pinned versions even if older exist
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--upgrade"],
            check=True,
            capture_output=False,
            text=True
        )
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during installation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_dependencies()
