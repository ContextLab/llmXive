"""
Script to verify and initialize linting/formatting configuration.
This script ensures that the project has the necessary configuration files
for ruff, black, and isort as defined in pyproject.toml.
"""
import os
import sys
from pathlib import Path

def check_file_exists(path: str) -> bool:
    """Check if a file exists relative to project root."""
    return Path(path).exists()

def main():
    """Verify linting configuration files exist."""
    project_root = Path(__file__).parent.parent
    config_files = [
        "pyproject.toml",
        ".flake8",
    ]

    missing = []
    for f in config_files:
        full_path = project_root / f
        if not full_path.exists():
            missing.append(f)
        else:
            print(f"[OK] Found configuration: {f}")

    if missing:
        print(f"[ERROR] Missing configuration files: {', '.join(missing)}")
        print("Please ensure 'pyproject.toml' and '.flake8' are present in the project root.")
        sys.exit(1)

    # Verify dependencies
    try:
        import ruff
        print("[OK] 'ruff' is installed.")
    except ImportError:
        print("[WARN] 'ruff' is not installed. Install with: pip install ruff")

    try:
        import black
        print("[OK] 'black' is installed.")
    except ImportError:
        print("[WARN] 'black' is not installed. Install with: pip install black")

    try:
        import isort
        print("[OK] 'isort' is installed.")
    except ImportError:
        print("[WARN] 'isort' is not installed. Install with: pip install isort")

    print("\nLinting and formatting tools are configured.")
    print("Run 'ruff check .' to lint and 'black .' to format.")

if __name__ == "__main__":
    main()
