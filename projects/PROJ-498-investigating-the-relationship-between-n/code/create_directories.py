#!/usr/bin/env python3
"""
Script to create the required project directory structure for PROJ-498.
This fulfills task T001: Create directory structure.
"""
from pathlib import Path
import sys

def create_directories() -> None:
    """
    Create the following directories relative to the repository root:

    projects/PROJ-498-investigating-the-relationship-between-n/
    projects/PROJ-498-investigating-the-relationship-between-n/code/
    projects/PROJ-498-investigating-the-relationship-between-n/data/
    projects/PROJ-498-investigating-the-relationship-between-n/tests/
    """
    base_path = Path("projects/PROJ-498-investigating-the-relationship-between-n")
    subdirs = ["code", "data", "tests"]

    try:
        # Ensure the base directory exists
        base_path.mkdir(parents=True, exist_ok=True)

        # Create each required subdirectory
        for sub in subdirs:
            (base_path / sub).mkdir(parents=True, exist_ok=True)

        print(f"Created directory structure under {base_path}")
    except Exception as e:
        print(f"Failed to create directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    create_directories()
