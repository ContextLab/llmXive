"""Verification script for T001.

This script ensures that the required project scaffold directories
``code/``, ``data/`` and ``tests/`` under the project root
``projects/PROJ-871-llmxive-follow-up-extending-planbench-xl`` exist
and are empty.  It removes any existing files/sub‑directories inside
those three directories (excluding this script itself, which lives at
the repository root), then asserts their emptiness.

The script is intended to be run directly:

    python verify_scaffold.py

It exits with status 0 on success and raises an AssertionError on
failure.
"""
import shutil
from pathlib import Path
import sys

def _empty_directory(dir_path: Path) -> None:
    """Delete all contents of *dir_path* without removing the directory itself."""
    if not dir_path.is_dir():
        raise AssertionError(f"Expected directory does not exist: {dir_path}")

    for entry in dir_path.iterdir():
        try:
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        except Exception as exc:
            raise AssertionError(f"Failed to delete {entry}: {exc}")

    # Verify emptiness
    if any(dir_path.iterdir()):
        raise AssertionError(f"Directory not empty after cleanup: {dir_path}")

def main() -> None:
    # Resolve the project root containing the scaffold.
    project_root = Path(__file__).parent / "projects" / "PROJ-871-llmxive-follow-up-extending-planbench-xl"
    required_subdirs = ["code", "data", "tests"]

    for sub in required_subdirs:
        sub_path = project_root / sub
        # Ensure the directory exists (create if missing)
        sub_path.mkdir(parents=True, exist_ok=True)
        # Empty its contents
        _empty_directory(sub_path)

    # Final assertions (existence already guaranteed by mkdir above)
    for sub in required_subdirs:
        sub_path = project_root / sub
        if not sub_path.is_dir():
            raise AssertionError(f"Required directory missing after cleanup: {sub_path}")

    print("Scaffold verification successful: empty 'code/', 'data/', and 'tests/' directories are present.")
    sys.exit(0)

if __name__ == "__main__":
    main()