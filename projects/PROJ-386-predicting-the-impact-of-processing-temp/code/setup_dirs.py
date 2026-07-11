import os
import sys
from pathlib import Path

def ensure_directory(path: str) -> bool:
    """
    Create a directory at the specified path if it does not exist.
    Returns True if the directory exists or was created successfully, False otherwise.
    """
    try:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point for creating project directories.
    Reads directory paths from command line arguments or a default list if none provided.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Create project directories")
    parser.add_argument(
        "paths",
        nargs="*",
        help="List of directory paths to create. If none provided, creates standard project dirs."
    )
    args = parser.parse_args()

    if not args.paths:
        # Default directories for the project
        default_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "artifacts/models",
            "artifacts/reports",
            "tests/unit"
        ]
        dirs_to_create = default_dirs
    else:
        dirs_to_create = args.paths

    success = True
    for d in dirs_to_create:
        if ensure_directory(d):
            print(f"Created/Verified: {d}")
        else:
            print(f"Failed to create: {d}", file=sys.stderr)
            success = False

    if not success:
        sys.exit(1)
    else:
        print("All directories ready.")

if __name__ == "__main__":
    main()
