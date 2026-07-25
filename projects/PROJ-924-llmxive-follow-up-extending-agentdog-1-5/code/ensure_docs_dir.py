import os
import sys
from pathlib import Path
from typing import Optional

from config import get_path, ensure_directories


def ensure_docs_directory(docs_path: Optional[str] = None) -> bool:
    """
    Create and verify the 'docs' directory for the project.

    Args:
        docs_path: Optional relative path for the docs directory.
                   Defaults to 'docs' if not provided.

    Returns:
        True if the directory exists and is writable after creation/verification.
        Raises an exception if creation fails or verification is impossible.
    """
    if docs_path is None:
        docs_path = "docs"

    base_path = get_path()
    target_dir = base_path / docs_path

    # Use the shared ensure_directories helper to create the path
    ensure_directories([target_dir])

    # Verify existence
    if not target_dir.exists():
        raise RuntimeError(f"Failed to create docs directory: {target_dir}")

    if not target_dir.is_dir():
        raise RuntimeError(f"Path exists but is not a directory: {target_dir}")

    # Verify writability by attempting to create a temporary marker file
    marker_file = target_dir / ".write_test_marker"
    try:
        marker_file.touch()
        marker_file.unlink()
    except PermissionError:
        raise RuntimeError(f"Docs directory exists but is not writable: {target_dir}")

    return True


def main() -> int:
    """
    Entry point for the script. Ensures the docs directory exists.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        print(f"Ensuring 'docs' directory exists at: {get_path() / 'docs'}")
        ensure_docs_directory()
        print("SUCCESS: 'docs' directory created and verified.")
        return 0
    except Exception as e:
        print(f"FAILURE: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
