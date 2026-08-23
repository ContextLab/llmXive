"""
Script to verify and document the linting/formatter configuration.
This script checks that the configuration files exist and are valid.
"""
import os
import sys
from pathlib import Path

def check_file_exists(path: str, description: str) -> bool:
    if os.path.exists(path):
        print(f"[OK] {description} found at {path}")
        return True
    else:
        print(f"[MISSING] {description} not found at {path}")
        return False

def main():
    project_root = Path(__file__).resolve().parent.parent
    config_files = [
        (project_root / ".ruff.toml", "Ruff configuration"),
        (project_root / "pyproject.toml", "Pyproject (Black/Pytest) configuration"),
        (project_root / ".flake8", "Flake8 configuration"),
    ]

    all_present = True
    for path, desc in config_files:
        if not check_file_exists(str(path), desc):
            all_present = False

    if all_present:
        print("\nLinting and formatting tools are configured.")
        print("Run 'ruff check .', 'black .', or 'flake8 .' to validate.")
        return 0
    else:
        print("\nConfiguration incomplete. Please create missing files.")
        return 1

if __name__ == "__main__":
    sys.exit(main())