"""
Setup script for creating and verifying 'state/' and 'docs/' directories.
Implements T004: Create state/ and docs/ directories.
"""
import os
import sys
from pathlib import Path


def setup_state_docs_directories(root_dir: Path) -> list:
    """
    Create the 'state' and 'docs' directories if they do not exist.

    Args:
        root_dir: The project root directory path.

    Returns:
        A list of created directory paths.
    """
    directories = [
        root_dir / "state",
        root_dir / "docs",
    ]
    created = []

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory))
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    return created


def verify_state_docs_directories(root_dir: Path) -> bool:
    """
    Verify that 'state' and 'docs' directories exist and are directories.

    Args:
        root_dir: The project root directory path.

    Returns:
        True if all directories exist and are directories, False otherwise.
    """
    directories = [
        root_dir / "state",
        root_dir / "docs",
    ]

    all_valid = True
    for directory in directories:
        if not directory.exists():
            print(f"FAIL: Directory does not exist: {directory}")
            all_valid = False
        elif not directory.is_dir():
            print(f"FAIL: Path exists but is not a directory: {directory}")
            all_valid = False
        else:
            print(f"PASS: Directory verified: {directory}")

    return all_valid


def main():
    """Main entry point for the script."""
    # Determine project root (assume script is in code/ or code/tasks/)
    script_path = Path(__file__).resolve()
    # Navigate up to project root (assuming structure: code/setup_state_docs.py -> root)
    root_dir = script_path.parent.parent

    print(f"Project root: {root_dir}")

    # Setup
    created = setup_state_docs_directories(root_dir)
    if created:
        print(f"Successfully created {len(created)} directories.")
    else:
        print("No new directories created (all already existed).")

    # Verification
    print("\nVerifying directories...")
    if verify_state_docs_directories(root_dir):
        print("\nVerification PASSED: All required directories exist.")
        return 0
    else:
        print("\nVerification FAILED: Some directories are missing or invalid.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
