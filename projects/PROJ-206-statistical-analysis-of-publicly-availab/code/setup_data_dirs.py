"""
Task T004: Setup data directory structure.

Creates the following directory structure relative to the project root:
- data/raw/
- data/processed/
- state/projects/

This script is idempotent and will not fail if directories already exist.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the required directory structure."""
    # Determine project root (assuming script is in code/ directory)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define required directories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
