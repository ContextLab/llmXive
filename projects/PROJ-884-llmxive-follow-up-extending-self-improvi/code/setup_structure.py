"""
Setup script to create the code/ directory hierarchy for the project.
Creates subdirectories: dataset, symbolic, bes, analysis, utils.
Verifies that all directories exist and are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

# Define the subdirectories to create under code/
CODE_SUBDIRS = [
    "dataset",
    "symbolic",
    "bes",
    "analysis",
    "utils"
]

def setup_code_directories(project_root: Path) -> List[Path]:
    """
    Create the code/ directory hierarchy and verify writability.

    Args:
        project_root: The root path of the project.

    Returns:
        A list of created directory paths.

    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    code_root = project_root / "code"
    created_dirs = []

    # Ensure the root code directory exists
    code_root.mkdir(parents=True, exist_ok=True)
    
    # Verify root code directory is writable
    try:
        test_file = code_root / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Code root directory '{code_root}' is not writable: {e}")

    # Create and verify subdirectories
    for subdir_name in CODE_SUBDIRS:
        subdir_path = code_root / subdir_name
        
        # Create the directory (parents=True to handle nested structures if needed)
        try:
            subdir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create directory '{subdir_path}': {e}")

        # Verify the directory is writable
        try:
            test_file = subdir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Directory '{subdir_path}' is not writable: {e}")

        created_dirs.append(subdir_path)
        print(f"Verified: {subdir_path}")

    return created_dirs

def main():
    """
    Main entry point for the setup script.
    Parses arguments and creates the directory structure.
    """
    parser = argparse.ArgumentParser(
        description="Create and verify the code/ directory hierarchy."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Path to the project root directory (default: current directory)."
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()

    print(f"Setting up code directories in: {project_root}")

    try:
        created_dirs = setup_code_directories(project_root)
        print(f"\nSuccessfully created and verified {len(created_dirs)} directories.")
        for d in created_dirs:
            print(f"  - {d}")
        return 0
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())