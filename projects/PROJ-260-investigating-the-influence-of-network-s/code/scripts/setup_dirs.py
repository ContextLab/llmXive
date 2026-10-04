import os
import sys
from pathlib import Path

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories required by T001a (data structure)
DATA_DIRS = [
    "data/raw",
    "data/derived",
    "data/derived/topology",
    "data/derived/vdos",
    "data/derived/reference",
    "data/derived/correlation",
    "data/metadata",
]

# Directories required by T001b (output structure)
OUTPUT_DIRS = [
    "outputs",
    "outputs/figures",
    "outputs/reports",
]

def create_directories():
    """
    Creates all required data and output directories defined in T001a and T001b.
    This function is idempotent (safe to run multiple times).
    """
    all_dirs = DATA_DIRS + OUTPUT_DIRS
    created_count = 0

    for dir_path in all_dirs:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            # Optional: verify it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    print(f"Directory setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the script."""
    try:
        create_directories()
    except Exception as e:
        print(f"Error during directory creation: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()