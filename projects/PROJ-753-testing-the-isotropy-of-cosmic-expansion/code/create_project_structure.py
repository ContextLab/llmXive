"""
create_project_structure.py
---------------------------

This script creates the required project directory tree for the
"Testing the Isotropy of Cosmic Expansion with Type Ia Supernova Data"
project.  It is intended to be run once (or repeatedly) from the
project root.  All directories are created with ``parents=True`` and
``exist_ok=True`` so the script is idempotent.

The directories created are:

- data/raw
- data/processed
- code
- tests/unit
- tests/integration
- tests/contract
- docs
- reports
- figures
- scripts

A ``.gitkeep`` file is added to each directory so that empty
directories are tracked by version control.
"""

import sys
from pathlib import Path

def _create_dir(path: Path) -> None:
    """Create a directory and a ``.gitkeep`` placeholder."""
    path.mkdir(parents=True, exist_ok=True)
    gitkeep = path / ".gitkeep"
    # Touch the .gitkeep file; it will be empty.
    gitkeep.touch(exist_ok=True)

def main() -> int:
    """Entry point for the directory‑creation script.

    Returns
    -------
    int
        Exit code (0 for success, non‑zero for failure).
    """
    try:
        project_root = Path.cwd()
        # List of directories relative to the project root.
        dirs = [
            project_root / "data" / "raw",
            project_root / "data" / "processed",
            project_root / "code",
            project_root / "tests" / "unit",
            project_root / "tests" / "integration",
            project_root / "tests" / "contract",
            project_root / "docs",
            project_root / "reports",
            project_root / "figures",
            project_root / "scripts",
        ]

        for d in dirs:
            _create_dir(d)

        print("Project directory tree created successfully.")
        return 0
    except Exception as exc:
        # Print the exception to stderr and return a non‑zero exit code.
        print(f"Error while creating directories: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())