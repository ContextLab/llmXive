"""
T002 Implementation: Create data subdirectories with 755 permissions.

This script creates the required subdirectories under the data/ folder:
- data/raw/
- data/processed/
- data/logs/

It ensures they have 755 permissions (rwxr-xr-x) as specified in the task.
"""

import os
import stat
import sys
from pathlib import Path
from typing import List, Tuple

# Import from existing project modules
from config import ensure_directories


def create_data_subdirectories(base_dir: Path = None) -> List[Tuple[Path, bool]]:
    """
    Create data subdirectories with 755 permissions.

    Args:
        base_dir: Base directory for data folder. Defaults to project root.

    Returns:
        List of tuples (path, created) indicating which directories were created.
    """
    if base_dir is None:
        base_dir = Path.cwd()

    # Ensure the base data directory exists first
    data_dir = base_dir / "data"
    ensure_directories(data_dir)

    # Define required subdirectories
    subdirs = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "logs",
    ]

    created_dirs = []

    for subdir in subdirs:
        created = False
        if not subdir.exists():
            subdir.mkdir(parents=True, exist_ok=True)
            created = True

        # Set permissions to 755 (rwxr-xr-x)
        # stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        desired_mode = 0o755
        current_mode = subdir.stat().st_mode & 0o777

        if current_mode != desired_mode:
            os.chmod(subdir, desired_mode)

        created_dirs.append((subdir, created))

    return created_dirs


def verify_directories(base_dir: Path = None) -> List[Tuple[Path, int, bool]]:
    """
    Verify that data subdirectories exist and have correct permissions.

    Args:
        base_dir: Base directory for data folder. Defaults to project root.

    Returns:
        List of tuples (path, permissions, is_valid) for verification.
    """
    if base_dir is None:
        base_dir = Path.cwd()

    data_dir = base_dir / "data"
    subdirs = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "logs",
    ]

    verification_results = []
    desired_mode = 0o755

    for subdir in subdirs:
        exists = subdir.exists()
        is_dir = subdir.is_dir() if exists else False
        valid_mode = False

        if exists and is_dir:
            current_mode = subdir.stat().st_mode & 0o777
            valid_mode = (current_mode == desired_mode)

        verification_results.append((subdir, desired_mode if valid_mode else -1, exists and is_dir and valid_mode))

    return verification_results


def main():
    """Main entry point for T002 implementation."""
    base_dir = Path.cwd()
    print(f"Creating data subdirectories in: {base_dir}")

    # Create directories
    created_results = create_data_subdirectories(base_dir)

    print("\nDirectory Creation Results:")
    for path, was_created in created_results:
        status = "Created" if was_created else "Already existed"
        print(f"  {path.relative_to(base_dir)}: {status}")

    # Verify directories
    print("\nVerification Results:")
    all_valid = True
    for path, expected_mode, is_valid in verify_directories(base_dir):
        status = "✓ Valid" if is_valid else "✗ Invalid"
        print(f"  {path.relative_to(base_dir)}: {status}")
        if not is_valid:
            all_valid = False

    if all_valid:
        print("\n✓ All data subdirectories created and verified with 755 permissions.")
        return 0
    else:
        print("\n✗ Some directories failed verification.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
