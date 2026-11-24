"""
Script to create the core directory layout required for the project.
Running this script will ensure that the following directories exist
relative to the project root:

- code/
  - data/
  - modeling/
  - utils/
  - cli/
- data/
  - raw/
  - interim/
  - processed/
- tests/

The script is idempotent: existing directories are left untouched.
"""

import sys
from pathlib import Path

def create_directories(root: Path, dirs):
    """Create each directory in ``dirs`` under ``root`` if it does not exist."""
    for d in dirs:
        dir_path = root / d
        dir_path.mkdir(parents=True, exist_ok=True)

def main():
    # Determine the project root (two levels up from this file):
    #   code/create_layout.py -> code/ -> project root
    project_root = Path(__file__).resolve().parents[1]

    # List of directories to create, relative to the project root
    directories = [
        "code",
        "code/data",
        "code/modeling",
        "code/utils",
        "code/cli",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests",
    ]

    create_directories(project_root, directories)

    # Simple verification output
    missing = [d for d in directories if not (project_root / d).is_dir()]
    if missing:
        print(f"ERROR: The following directories were not created: {missing}", file=sys.stderr)
        sys.exit(1)
    else:
        print("Core directory layout created successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()