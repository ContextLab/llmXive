"""
init_project_structure.py
-------------------------

This script initializes the required project directory structure for the
`PROJ-430-the-impact-of-asynchronous-communication` feature branch.

It creates the following sub‑directories under the project root:

    projects/PROJ-430-the-impact-of-asynchronous-communication/
        code/
        data/
        tests/
        docs/
        config/

After creation, it prints a simple directory tree to standard output so
that the verification step (`test -d …`) can be performed manually or by
an automated test harness.

The script is idempotent – running it multiple times will not raise
errors because `exist_ok=True` is used for all directory creations.
"""

import os
from pathlib import Path
import sys

# Root of the feature project (relative to repository root)
PROJECT_ROOT = Path("projects/PROJ-430-the-impact-of-asynchronous-communication")

# Sub‑directories that must exist
REQUIRED_SUBDIRS = [
    "code",
    "data",
    "tests",
    "docs",
    "config",
]

def create_directories(root: Path, subdirs: list[str]) -> None:
    """Create each sub‑directory under ``root``."""
    for sub in subdirs:
        dir_path = root / sub
        dir_path.mkdir(parents=True, exist_ok=True)

def print_directory_tree(root: Path) -> None:
    """Print a simple tree view of ``root``."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Compute depth for indentation
        depth = len(Path(dirpath).relative_to(root).parts)
        indent = "│   " * depth
        print(f"{indent}├── {Path(dirpath).name}")
        # Print files (if any) – not required for this task but useful for debugging
        for fname in sorted(filenames):
            file_indent = "│   " * (depth + 1)
            print(f"{file_indent}└── {fname}")

def main() -> int:
    """Entry point for the script."""
    try:
        # Ensure the root directory itself exists
        PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

        # Create required sub‑directories
        create_directories(PROJECT_ROOT, REQUIRED_SUBDIRS)

        # Output the resulting directory tree
        print("Project directory structure:")
        print_directory_tree(PROJECT_ROOT)

        # Successful execution
        return 0
    except Exception as exc:
        # Log the exception to stderr and exit with non‑zero status
        print(f"Error initializing project structure: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
