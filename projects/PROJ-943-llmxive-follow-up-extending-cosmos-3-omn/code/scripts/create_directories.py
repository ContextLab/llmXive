"""
Script to create standard project directories and ensure .gitkeep files exist.
This ensures version control persistence for empty directories.
"""
import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
# Assuming this script runs from the 'code' directory or we resolve relative to script location
REQUIRED_DIRS = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/splits",
    "models",
    "tests",
    "reports",
    "utils"
]

GITKEEP_CONTENT = "# Placeholder to ensure directory exists in git\n"

def create_directory(base_path: Path, dir_name: str) -> bool:
    """Create a directory and its .gitkeep file if it doesn't exist."""
    full_path = base_path / dir_name
    try:
        full_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text(GITKEEP_CONTENT)
            print(f"Created: {full_path} with .gitkeep")
        else:
            print(f"Exists: {full_path} (with .gitkeep)")
        return True
    except Exception as e:
        print(f"Error creating {full_path}: {e}", file=sys.stderr)
        return False

def main():
    # Determine the base path: usually the directory containing this script's parent (project root 'code')
    # If run as 'python code/scripts/create_directories.py', __file__ is code/scripts/...
    script_path = Path(__file__).resolve()
    base_path = script_path.parent  # This is 'code'

    print(f"Creating directories under: {base_path}")
    success = True
    for dir_name in REQUIRED_DIRS:
        if not create_directory(base_path, dir_name):
            success = False

    if success:
        print("\nAll required directories and .gitkeep files are ready.")
    else:
        print("\nSome directories failed to create.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
