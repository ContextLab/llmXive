import os
from pathlib import Path
from typing import Optional

from config import get_path, ensure_directories

def ensure_specs_directory(base_path: Optional[str] = None) -> bool:
    """
    Ensure the 'specs' directory exists under the project root.

    Args:
        base_path: Optional override for the project root path.
                   If None, uses the path defined in config.

    Returns:
        True if the directory was successfully created or already exists.
        Raises an exception if creation fails.
    """
    project_root = get_path(base_path)
    specs_dir = project_root / "specs"

    # Use the shared ensure_directories helper to create the path
    # This will raise an error if creation fails
    ensure_directories([specs_dir])

    return True

def main() -> int:
    """
    Main entry point for the script.
    Creates the specs directory and verifies its existence.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        print("Creating specs directory...")
        ensure_specs_directory()
        print("Specs directory created successfully.")
        return 0
    except Exception as e:
        print(f"Error creating specs directory: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
