import os
import sys
from pathlib import Path

def get_project_root():
    """Return the project root directory."""
    # Assuming the script is run from code/ directory
    current = Path(__file__).resolve()
    return current.parent.parent

def main():
    """Create the required data directory structure."""
    root = get_project_root()
    data_root = root / "data"

    # Define required subdirectories
    dirs = [
        data_root / "raw",
        data_root / "interim",
        data_root / "processed",
        data_root / "figures"
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {d}")

    # Verify creation
    missing = [d for d in dirs if not d.exists()]
    if missing:
        print(f"Error: Failed to create directories: {missing}")
        sys.exit(1)
    else:
        print("All data directories successfully created.")

if __name__ == "__main__":
    main()
