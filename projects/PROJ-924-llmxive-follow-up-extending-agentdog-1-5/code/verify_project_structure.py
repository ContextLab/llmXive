"""
Verification script for llmXive project structure.
Checks that all required directories and key files exist.
"""
import os
import sys
from pathlib import Path


def verify_structure(base_path: Path = None) -> bool:
    """
    Verify the existence of required project directories.

    Args:
        base_path: Root directory of the project.

    Returns:
        True if all required structures exist, False otherwise.
    """
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent

    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/test",
        "specs",
        "docs",
        "specs/001-llmxive-drift-detection"
    ]

    all_exist = True

    print(f"Verifying project structure at: {base_path}")
    print("-" * 50)

    for dir_path in required_dirs:
        full_path = base_path / dir_path
        exists = full_path.exists() and full_path.is_dir()
        status = "✓" if exists else "✗"
        print(f"{status} {dir_path}")

        if not exists:
            all_exist = False

    print("-" * 50)

    if all_exist:
        print("All required directories exist.")
    else:
        print("ERROR: Some required directories are missing.")

    return all_exist


def main():
    """Main entry point for verification script."""
    base_path = Path(__file__).resolve().parent.parent
    success = verify_structure(base_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
