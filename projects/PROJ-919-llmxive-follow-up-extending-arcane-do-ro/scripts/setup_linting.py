"""
Script to verify and initialize linting and formatting tools.
This script ensures that the configuration files are present and
dependencies are installed.
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    root = Path(__file__).parent.parent
    config_files = [
        "pyproject.toml",
        "ruff.toml",
        ".pre-commit-config.yaml",
        "requirements.txt"
    ]

    missing = [f for f in config_files if not (root / f).exists()]
    if missing:
        print(f"Error: Missing configuration files: {missing}")
        sys.exit(1)

    print("Configuration files found.")

    # Check if tools are installed
    try:
        subprocess.run([sys.executable, "-m", "ruff", "--version"], check=True, capture_output=True)
        print("Ruff is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Ruff not found. Install via: pip install ruff")

    try:
        subprocess.run([sys.executable, "-m", "black", "--version"], check=True, capture_output=True)
        print("Black is installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: Black not found. Install via: pip install black")

    print("Linting and formatting configuration verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())