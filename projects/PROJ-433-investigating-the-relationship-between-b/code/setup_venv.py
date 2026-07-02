"""
Setup Python virtual environment for the project.

This script creates a virtual environment at the repository root using Python 3.11.
It is idempotent: if the environment already exists, it is skipped.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """Create the virtual environment if it doesn't exist."""
    repo_root = Path(__file__).resolve().parent.parent
    venv_path = repo_root / "venv"

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return 0

    print(f"Creating virtual environment at {venv_path} using {sys.executable}...")
    
    # Check Python version
    version = sys.version_info
    if version.major != 3 or version.minor < 11:
        print(f"Warning: Python 3.11+ is recommended. Current version: {version.major}.{version.minor}")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"Successfully created virtual environment at {venv_path}")
        print("Next steps:")
        print(f"  1. Activate: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)")
        print(f"  2. Install dependencies: pip install -r code/requirements.txt")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e.stderr.decode()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())