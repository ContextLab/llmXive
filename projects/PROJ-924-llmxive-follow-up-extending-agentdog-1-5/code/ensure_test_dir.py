import os
import sys
from pathlib import Path
from typing import Optional

from config import get_path, ensure_directories


def ensure_test_directory(path: Optional[Path] = None) -> Path:
    """
    Create and verify the existence of the data/test directory.

    Args:
        path: Optional custom path. If None, uses the project's data/test path
              defined in config.

    Returns:
        The absolute Path to the created/verified directory.

    Raises:
        RuntimeError: If the directory cannot be created or verified.
    """
    base_path = path or get_path("data_test")
    
    # Ensure the parent 'data' directory exists first
    parent_dir = base_path.parent
    if not parent_dir.exists():
        parent_dir.mkdir(parents=True, exist_ok=True)
    
    # Create the specific test directory
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Verify existence
    if not base_path.exists() or not base_path.is_dir():
        raise RuntimeError(
            f"Failed to create or verify directory: {base_path}"
        )
    
    return base_path


def main() -> int:
    """
    Entry point for ensuring the test directory exists.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        test_dir = ensure_test_directory()
        print(f"Verified directory: {test_dir}")
        return 0
    except Exception as e:
        print(f"Error ensuring test directory: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
