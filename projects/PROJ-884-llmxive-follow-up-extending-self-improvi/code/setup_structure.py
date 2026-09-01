"""
Script to set up the code directory hierarchy for the llmXive project.
Creates the required subdirectories under code/ and verifies they are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

# Define the required subdirectories for the code/ hierarchy
REQUIRED_SUBDIRS = [
    "dataset",
    "symbolic",
    "bes",
    "analysis",
    "utils"
]

def setup_code_directories(base_path: Path) -> List[Path]:
    """
    Create the code/ directory hierarchy and verify writability.

    Args:
        base_path: The project root path where the 'code' directory will be created.

    Returns:
        List of created directory paths.

    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    code_dir = base_path / "code"
    created_dirs = []

    # Ensure the base 'code' directory exists
    if not code_dir.exists():
        try:
            code_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {code_dir}")
        except OSError as e:
            raise RuntimeError(f"Failed to create base code directory {code_dir}: {e}")

    # Verify the base code directory is writable
    test_file = code_dir / ".write_test"
    try:
        test_file.touch(exist_ok=True)
        test_file.unlink()
    except OSError as e:
        raise RuntimeError(f"Base code directory {code_dir} is not writable: {e}")

    # Create and verify subdirectories
    for subdir_name in REQUIRED_SUBDIRS:
        subdir_path = code_dir / subdir_name
        
        if not subdir_path.exists():
            try:
                subdir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {subdir_path}")
            except OSError as e:
                raise RuntimeError(f"Failed to create subdirectory {subdir_path}: {e}")
        
        # Verify writability of the subdirectory
        test_file = subdir_path / ".write_test"
        try:
            test_file.touch(exist_ok=True)
            test_file.unlink()
            created_dirs.append(subdir_path)
        except OSError as e:
            raise RuntimeError(f"Subdirectory {subdir_path} is not writable: {e}")

    print(f"\nSuccessfully created and verified {len(created_dirs)} subdirectories under {code_dir}")
    return created_dirs

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Set up the code directory hierarchy for the llmXive project."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Path to the project root directory (default: current directory)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()
    project_root = args.project_root.resolve()

    if args.verbose:
        print(f"Project root: {project_root}")
        print(f"Target code directory: {project_root / 'code'}")

    try:
        setup_code_directories(project_root)
        print("\n✅ Directory hierarchy setup complete.")
        return 0
    except RuntimeError as e:
        print(f"\n❌ Error during setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
