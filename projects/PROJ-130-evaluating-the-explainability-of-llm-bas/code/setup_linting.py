"""
Setup script to initialize linting and formatting tools.
This script verifies configuration files exist and provides instructions for
installing and activating pre-commit hooks.
"""
import os
import sys
from pathlib import Path

def main():
    root_dir = Path(__file__).parent.parent
    config_files = [
        ".ruff.toml",
        "pyproject.toml",
        ".pre-commit-config.yaml",
        "code/requirements.txt",
    ]

    print("Checking linting and formatting configuration...")
    all_present = True
    for cfg in config_files:
        path = root_dir / cfg
        if path.exists():
            print(f"  ✓ {cfg} found")
        else:
            print(f"  ✗ {cfg} MISSING")
            all_present = False

    if all_present:
        print("\nConfiguration files are present.")
        print("\nTo enable automatic linting and formatting on git commit:")
        print("  1. Install dependencies: pip install -r code/requirements.txt")
        print("  2. Install pre-commit hooks: pre-commit install")
        print("  3. Run hooks on all files: pre-commit run --all-files")
        print("\nTo run manually:")
        print("  - Lint: ruff check .")
        print("  - Format: black .")
        return 0
    else:
        print("\nERROR: Missing configuration files. Please ensure T005 is completed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
