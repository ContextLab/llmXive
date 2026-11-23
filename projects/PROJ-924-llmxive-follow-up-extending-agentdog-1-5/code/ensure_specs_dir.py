import os
import sys
from pathlib import Path

from config import get_path, ensure_directories

def ensure_specs_directory(base_path: str = None) -> bool:
    """
    Ensure the specs directory exists.

    Args:
        base_path: Optional base path override.

    Returns:
        True if directory exists or was created.
    """
    project_root = get_path(base_path)
    specs_dir = project_root / "specs"
    ensure_directories([specs_dir])
    return True

def main() -> int:
    """Main entry point."""
    try:
        print("Ensuring specs directory exists...")
        ensure_specs_directory()
        print("Specs directory verified.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())