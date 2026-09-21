"""
Setup script to create the tests directory hierarchy.
Creates tests/unit and tests/integration directories and verifies they are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_tests_directories(project_root: Path) -> List[Path]:
    """
    Create the tests directory structure.
    
    Args:
        project_root: The root directory of the project.
        
    Returns:
        List of created directory paths.
        
    Raises:
        OSError: If directories cannot be created or are not writable.
    """
    tests_root = project_root / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    
    directories = [tests_root, unit_dir, integration_dir]
    
    for directory in directories:
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # Verify writability by creating a temporary file
                test_file = directory / ".write_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                except OSError as e:
                    raise OSError(f"Directory {directory} exists but is not writable: {e}")
            except OSError as e:
                raise OSError(f"Failed to create directory {directory}: {e}")
    
    return directories

def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Setup tests directory hierarchy for llmXive project."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to the project root directory (default: current directory)."
    )
    
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    
    print(f"Setting up tests directories in: {project_root}")
    
    try:
        directories = setup_tests_directories(project_root)
        print("Successfully created the following directories:")
        for directory in directories:
            print(f"  - {directory}")
        print("All directories are writable.")
        return 0
    except OSError as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
