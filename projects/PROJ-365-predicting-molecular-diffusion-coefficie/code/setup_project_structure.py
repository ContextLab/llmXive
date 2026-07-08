"""
setup_project_structure.py

Script to create the required project directory structure and initialize
an empty checksums.json file as specified in the project plan.

Running this script (or importing and calling ``main``) will ensure the
following paths exist relative to the project root:

- code/
- data/raw/
- data/processed/
- data/logs/
- data/artifacts/
- data/checksums.json  (initialized to an empty JSON object if missing)
"""

import json
from pathlib import Path
from utils.config import get_project_root

def _ensure_directory(path: Path) -> None:
    """Create a directory and all parent directories if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)

def _ensure_checksums_file(path: Path) -> None:
    """Create an empty checksums.json file if it does not exist."""
    if not path.exists():
        # Write an empty JSON object to initialise the file.
        path.write_text(json.dumps({}, indent=2))

def create_project_structure() -> None:
    """
    Create the full project structure required by the plan.

    Directories:
        code/
        data/raw/
        data/processed/
        data/logs/
        data/artifacts/

    Files:
        data/checksums.json
    """
    root = get_project_root()

    # Define required directories
    required_dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "logs",
        root / "data" / "artifacts",
    ]

    for d in required_dirs:
        _ensure_directory(d)

    # Ensure the checksums.json file exists
    checksums_path = root / "data" / "checksums.json"
    _ensure_checksums_file(checksums_path)

def main() -> None:
    """Entry‑point for ``python -m code.setup_project_structure``."""
    create_project_structure()

if __name__ == "__main__":
    main()
