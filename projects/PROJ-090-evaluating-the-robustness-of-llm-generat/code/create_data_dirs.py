"""
Script to create the required data directory hierarchy for the project.
This satisfies task T002 by ensuring the following subdirectories exist
under the project root's `data/` folder:
  - data/raw/
  - data/processed/
  - data/logs/
The script is idempotent and can be safely re‑run; it will create any
missing directories and leave existing ones untouched.
"""

import sys
from pathlib import Path


def create_directories() -> None:
    """Create the data sub‑directories if they do not already exist."""
    base_dir = Path("data")
    subdirs = ["raw", "processed", "logs"]

    for sub in subdirs:
        dir_path = base_dir / sub
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            print(f"Failed to create directory {dir_path!s}: {exc}", file=sys.stderr)
            raise

    # Verification output (optional but helpful)
    created = ", ".join(str(base_dir / sub) for sub in subdirs)
    print(f"Created/verified data directories: {created}")


def main() -> int:
    """Entry point for the script."""
    try:
        create_directories()
        return 0
    except Exception:
        return 1


if __name__ == "__main__":
    sys.exit(main())