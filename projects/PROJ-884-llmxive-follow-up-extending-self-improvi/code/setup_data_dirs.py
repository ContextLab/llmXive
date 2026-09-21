"""
Setup script to create and verify the data directory structure.
Creates: data/raw (immutable puzzles) and data/processed (logs/results).
Verifies existence and writability.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assumes script is run from project root or code/
    current = Path.cwd()
    if current.name == "code":
        return current.parent
    return current

def setup_data_directories(project_root: Path) -> List[Path]:
    """
    Create data/raw and data/processed directories if they don't exist.
    Returns the list of created/verified directories.
    """
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"

    dirs_to_create = [data_root, raw_dir, processed_dir]

    created_or_verified = []

    for directory in dirs_to_create:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
        
        # Verify writability by attempting to create a temporary file
        test_file = directory / ".write_test"
        try:
            test_file.touch(exist_ok=True)
            test_file.unlink()
            created_or_verified.append(directory)
            print(f"Verified writability: {directory}")
        except OSError as e:
            print(f"ERROR: Directory {directory} is not writable: {e}", file=sys.stderr)
            raise RuntimeError(f"Directory {directory} is not writable") from e

    return created_or_verified

def main():
    parser = argparse.ArgumentParser(
        description="Setup data directory structure for llmXive project."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to project root (default: current directory or parent if in code/)"
    )
    args = parser.parse_args()

    project_root = args.project_root if args.project_root else get_project_root()
    print(f"Project root: {project_root}")

    try:
        verified_dirs = setup_data_directories(project_root)
        print(f"Successfully setup and verified {len(verified_dirs)} directories.")
        for d in verified_dirs:
            print(f"  - {d}")
        return 0
    except Exception as e:
        print(f"Failed to setup data directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
