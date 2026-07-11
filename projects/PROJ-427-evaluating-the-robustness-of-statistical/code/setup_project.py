"""Create the required project directory structure for PROJ-427.

Running this script will ensure the following tree exists relative to the
repository root:

    data/
        raw/
        corrupted/
    code/
    results/
    tests/

It also creates empty ``__init__.py`` files in ``code/`` and ``tests/``
so that they are recognised as Python packages.

The script is idempotent – existing directories or files are left
untouched.
"""

import argparse
from pathlib import Path
import sys

def create_dir(path: Path) -> None:
    """Create a directory if it does not already exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def create_init_file(package_path: Path) -> None:
    """Create an empty __init__.py file inside the given package path."""
    init_file = package_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"Created __init__.py: {init_file}")
    else:
        print(f"__init__.py already exists: {init_file}")

def main() -> int:
    """Entry point for the setup script."""
    root = Path(__file__).resolve().parents[1]  # repository root
    # Define required directories
    dirs = [
        root / "data" / "raw",
        root / "data" / "corrupted",
        root / "code",
        root / "results",
        root / "tests",
    ]

    for d in dirs:
        create_dir(d)

    # Ensure package init files
    create_init_file(root / "code")
    create_init_file(root / "tests")

    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create project directory structure for PROJ-427."
    )
    # No additional arguments needed; script is self‑contained.
    args = parser.parse_args()
    sys.exit(main())