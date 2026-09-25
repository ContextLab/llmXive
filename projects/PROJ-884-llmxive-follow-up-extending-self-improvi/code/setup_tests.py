"""
Setup script to create the tests directory hierarchy.
Creates tests/unit and tests/integration directories and verifies they exist and are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    # If running from code/setup_tests.py, go up two levels
    current_file = Path(__file__).resolve()
    # Try to find the root by looking for a known marker or just going up
    # Standard structure: projects/PROJ-.../code/setup_tests.py
    # We assume the project root is the parent of the 'code' directory
    if current_file.name == "setup_tests.py":
        code_dir = current_file.parent
        if code_dir.name == "code":
            return code_dir.parent

    # Fallback: assume current working directory is project root
    return Path.cwd()


def setup_tests_directories(root_dir: Path) -> List[Path]:
    """
    Create the tests directory hierarchy: tests/unit and tests/integration.
    Verifies that the directories exist and are writable.

    Args:
        root_dir: The project root directory.

    Returns:
        A list of created directory paths.

    Raises:
        OSError: If a directory cannot be created or is not writable.
    """
    tests_base = root_dir / "tests"
    unit_dir = tests_base / "unit"
    integration_dir = tests_base / "integration"

    directories = [tests_base, unit_dir, integration_dir]

    for directory in directories:
        # Create the directory if it doesn't exist, including parents
        directory.mkdir(parents=True, exist_ok=True)
        
        # Verify existence
        if not directory.exists():
            raise OSError(f"Failed to create directory: {directory}")
        
        if not directory.is_dir():
            raise OSError(f"Path exists but is not a directory: {directory}")

        # Verify writability by attempting to create a temporary file
        test_file = directory / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            # Clean up
            test_file.unlink()
        except (IOError, PermissionError) as e:
            raise OSError(f"Directory {directory} is not writable: {e}")

    return directories


def main():
    """
    Main entry point for the setup script.
    """
    parser = argparse.ArgumentParser(
        description="Setup tests directory hierarchy (tests/unit, tests/integration)"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root directory (default: auto-detect or cwd)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    root = args.root if args.root else get_project_root()

    if args.verbose:
        print(f"Project root detected: {root}")

    try:
        created_dirs = setup_tests_directories(root)
        if args.verbose:
            print(f"Successfully created/verified {len(created_dirs)} directories:")
            for d in created_dirs:
                print(f"  - {d}")
        print("Tests directory hierarchy setup complete.")
        return 0
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
