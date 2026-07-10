"""
Data Directory Structure Setup Module.

This module ensures the required directory structure for the research pipeline
exists, specifically:
- data/raw/ (immutable storage for raw session logs)
- data/processed/ (storage for cleaned data and analysis results)

It also sets appropriate permissions to enforce immutability on the raw data
directory where possible.
"""
import os
import stat
import sys
from pathlib import Path
from typing import List, Optional

# Import from sibling utils to ensure consistent project root resolution
# We assume the project root is the parent of 'code'
def get_project_root() -> Path:
    """Determine the project root directory."""
    current_file = Path(__file__).resolve()
    # Project root is typically two levels up from code/setup/setup_data_dirs.py
    # or we can look for a marker file.
    # Standard convention: <root>/code/setup/...
    root = current_file.parent.parent.parent
    return root

def ensure_directory(path: Path, make_immutable: bool = False) -> bool:
    """
    Ensure a directory exists. If it doesn't, create it.

    Args:
        path: The Path object for the directory to ensure.
        make_immutable: If True, attempt to remove write permissions
                        on the directory to enforce immutability.

    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            if make_immutable:
                # Remove write permissions for owner, group, and others
                # This is a best-effort approach for immutability on POSIX systems
                current_perms = path.stat().st_mode
                # Remove write bits: w = 2 (owner), 2 (group), 2 (others) -> 0o222
                # We want to keep read (4) and execute (1) for directories.
                # New mode = old mode & ~0o222
                read_exec_only = current_perms & ~0o222
                os.chmod(path, read_exec_only)
            return True
        return True
    except PermissionError:
        print(f"Permission denied: Could not create or modify permissions for {path}")
        return False
    except Exception as e:
        print(f"Error ensuring directory {path}: {e}")
        return False

def main() -> None:
    """
    Main entry point to set up the data directory structure.
    Creates:
    - data/raw/ (immutable)
    - data/processed/
    """
    root = get_project_root()
    data_dir = root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    print(f"Project Root: {root}")
    print(f"Setting up data directories in: {data_dir}")

    success = True

    # Ensure base data directory
    if not ensure_directory(data_dir):
        success = False

    # Ensure raw directory (immutable)
    if not ensure_directory(raw_dir, make_immutable=True):
        success = False
    else:
        print(f"Created/Verified: {raw_dir} (immutable)")

    # Ensure processed directory
    if not ensure_directory(processed_dir):
        success = False
    else:
        print(f"Created/Verified: {processed_dir}")

    if success:
        print("Data directory structure setup complete.")
    else:
        print("Data directory structure setup failed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()