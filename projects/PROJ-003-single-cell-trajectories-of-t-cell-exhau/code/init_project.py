#!/usr/bin/env python
"""
Init script for establishing the project layout required by T001.
It creates the standard directory tree (code/, data/raw/, data/processed/,
data/results/, tests/unit/, tests/integration/) and copies the quickstart
documentation to the project root.
"""
import shutil
import sys
from pathlib import Path

# Import the helper that creates the directory structure.
# This function is defined in `code/setup_directories.py`.
from setup_directories import setup_directories

def main() -> None:
    # Determine the project root (two levels up from this file).
    project_root = Path(__file__).resolve().parents[1]

    # 1. Create the required directories.
    # The helper uses the current working directory; ensure we are at the
    # project root when invoking it.
    cwd = Path.cwd()
    if cwd != project_root:
        # Change to the project root so that relative paths inside the helper
        # resolve correctly.
        try:
            cwd.chdir()
        except Exception:
            # Fallback: temporarily change the working directory.
            import os
            os.chdir(project_root)

    setup_directories()

    # 2. Copy the quickstart documentation from the specs folder to the
    # project root (as required by the task description).
    src_quickstart = project_root / "specs" / "001-single-cell-trajectories-of-t-cell-exhau" / "quickstart.md"
    dst_quickstart = project_root / "quickstart.md"

    if not src_quickstart.is_file():
        sys.stderr.write(f"Source quickstart.md not found at {src_quickstart}\\n")
        sys.exit(1)

    try:
        shutil.copyfile(src_quickstart, dst_quickstart)
        print(f"Copied quickstart.md to {dst_quickstart}")
    except Exception as e:
        sys.stderr.write(f"Failed to copy quickstart.md: {e}\\n")
        sys.exit(1)

    print("Project layout initialized successfully.")

if __name__ == "__main__":
    main()
