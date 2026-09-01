"""
Setup script for creating the tests directory hierarchy.
Creates tests/unit and tests/integration directories and verifies they are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_tests_directories(base_path: Path) -> List[Path]:
    """
    Create the tests directory hierarchy: tests/unit and tests/integration.
    
    Args:
        base_path: The root directory where tests/ should be created.
        
    Returns:
        List of created directory paths.
        
    Raises:
        OSError: If directories cannot be created or are not writable.
    """
    tests_dir = base_path / "tests"
    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"
    
    directories = [tests_dir, unit_dir, integration_dir]
    
    for directory in directories:
        # Create directory if it doesn't exist, including parents
        directory.mkdir(parents=True, exist_ok=True)
        
        # Verify the directory exists
        if not directory.exists():
            raise OSError(f"Failed to create directory: {directory}")
        
        # Verify the directory is writable by creating a test file
        test_file = directory / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError) as e:
            raise OSError(f"Directory {directory} is not writable: {e}")
        
        print(f"Verified: {directory} exists and is writable")
    
    return directories

def main():
    """Main entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Setup tests directory hierarchy"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path where tests directory will be created (default: current directory)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    try:
        created_dirs = setup_tests_directories(args.base_path)
        
        if args.verbose:
            print(f"\nSuccessfully created {len(created_dirs)} directories:")
            for d in created_dirs:
                print(f"  - {d}")
        
        print("\nTests directory hierarchy setup complete.")
        return 0
        
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
