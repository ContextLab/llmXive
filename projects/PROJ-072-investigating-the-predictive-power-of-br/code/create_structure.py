"""
Script to create the required project directory structure.
This script is part of task T001 and is executed to ensure that all
necessary folders exist before proceeding to later phases.
"""
import sys
from pathlib import Path

def create_dir(relative_path: str) -> None:
    """
    Create a directory (and any missing parents) safely.

    Args:
        relative_path: Path relative to the project root.
    """
    path = Path(relative_path)
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    # Directories required by the implementation plan (excluding the platform‑owned `state/` folder)
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/metadata",
        "tests",
        "docs",
        "scripts"
    ]

    for d in required_dirs:
        create_dir(d)

    # Inform the user / logging system that creation succeeded
    print("Project structure created successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error creating project structure: {exc}", file=sys.stderr)
        sys.exit(1)
