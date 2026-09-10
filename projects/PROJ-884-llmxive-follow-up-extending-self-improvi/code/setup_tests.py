import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_tests_directories(base_path: Path) -> List[Path]:
    """
    Create the tests directory hierarchy:
    - tests/
    - tests/unit/
    - tests/integration/
    
    Verifies that directories exist and are writable.
    
    Args:
        base_path: The project root path where tests/ should be created.
        
    Returns:
        List of created directory paths.
        
    Raises:
        OSError: If a directory cannot be created or is not writable.
    """
    directories = [
        base_path / "tests",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        # Create directory if it doesn't exist
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify the directory exists
        if not dir_path.exists():
            raise OSError(f"Failed to create directory: {dir_path}")
        
        # Verify the directory is a directory
        if not dir_path.is_dir():
            raise OSError(f"Path exists but is not a directory: {dir_path}")
        
        # Verify write permissions by creating a temporary file
        test_file = dir_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            raise OSError(f"Directory is not writable: {dir_path}")
        
        created_dirs.append(dir_path)
        print(f"Verified: {dir_path} (exists and writable)")
    
    return created_dirs

def main():
    """
    CLI entry point for setting up tests directories.
    """
    parser = argparse.ArgumentParser(
        description="Create and verify tests directory hierarchy"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current working directory)"
    )
    
    args = parser.parse_args()
    
    try:
        created = setup_tests_directories(args.project_root)
        print(f"\nSuccessfully created {len(created)} directories.")
        return 0
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
