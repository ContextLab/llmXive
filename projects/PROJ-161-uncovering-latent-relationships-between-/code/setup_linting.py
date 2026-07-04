"""
Setup script to initialize linting and formatting tools.
This script verifies the presence of configuration files and
provides instructions for installing dependencies.
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists in the project root."""
    return Path(filepath).exists()

def main():
    """Verify linting configuration files."""
    root = Path(__file__).parent.parent
    config_files = [
        ".flake8",
        "pyproject.toml",
        ".pre-commit-config.yaml",
        "requirements-dev.txt"
    ]

    print("Checking linting configuration files...")
    all_present = True
    for fname in config_files:
        fpath = root / fname
        if fpath.exists():
            print(f"  ✓ {fname} found")
        else:
            print(f"  ✗ {fname} MISSING")
            all_present = False

    if all_present:
        print("\nLinting configuration is complete.")
        print("To install dev dependencies, run:")
        print("  pip install -r requirements-dev.txt")
        print("\nTo run pre-commit hooks manually:")
        print("  pre-commit run --all-files")
        return 0
    else:
        print("\nError: Some configuration files are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())