"""
Setup script to create the tests directory hierarchy.
Creates tests/ with unit/ and integration/ subdirectories.
Verifies directories exist and are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_tests_directories(base_path: Path) -> List[Path]:
    """
    Create the tests directory hierarchy.
    
    Args:
        base_path: The project root directory.
        
    Returns:
        List of created directory paths.
        
    Raises:
        OSError: If a directory cannot be created or verified.
    """
    tests_root = base_path / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    
    dirs_to_create = [tests_root, unit_dir, integration_dir]
    created_dirs = []
    
    for dir_path in dirs_to_create:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            
            # Verify the directory is writable by creating a temporary file
            test_file = dir_path / ".write_test"
            try:
                with open(test_file, 'w') as f:
                    f.write("writable")
                # Clean up the test file
                test_file.unlink()
            except IOError as e:
                raise OSError(f"Directory {dir_path} is not writable: {e}")
                
        except OSError as e:
            raise OSError(f"Failed to create directory {dir_path}: {e}")
            
    return created_dirs

def main():
    parser = argparse.ArgumentParser(
        description="Setup tests directory hierarchy for the project."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to the project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    base_path = Path(args.project_root).resolve()
    
    print(f"Setting up tests directory hierarchy in: {base_path}")
    
    try:
        created_dirs = setup_tests_directories(base_path)
        print("Successfully created directories:")
        for d in created_dirs:
            print(f"  - {d}")
        print("Verification: All directories are writable.")
        return 0
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
