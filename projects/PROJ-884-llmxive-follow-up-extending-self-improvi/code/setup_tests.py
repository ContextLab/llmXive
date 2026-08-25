import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_tests_directories() -> List[str]:
    """
    Creates the tests directory hierarchy: tests/{unit,integration}.
    Verifies that directories exist and are writable by creating a .gitkeep file.
    
    Returns:
        List[str]: List of created directory paths.
    """
    base_dir = Path(__file__).resolve().parent.parent
    tests_root = base_dir / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"
    
    directories = [tests_root, unit_dir, integration_dir]
    created_paths = []
    
    for dir_path in directories:
        try:
            # Create directory if it doesn't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Verify writability by creating a .gitkeep file
            keep_file = dir_path / ".gitkeep"
            keep_file.write_text("# Keep directory in git\n")
            
            # Verify the file exists and is readable/writable
            if not keep_file.exists():
                raise IOError(f"Failed to create .gitkeep in {dir_path}")
            
            # Clean up the test file
            keep_file.unlink()
            
            created_paths.append(str(dir_path))
            print(f"Verified: {dir_path} exists and is writable.")
            
        except PermissionError:
            print(f"Error: Permission denied when creating {dir_path}")
            raise
        except OSError as e:
            print(f"Error: OS error when creating {dir_path}: {e}")
            raise
    
    return created_paths

def main():
    """Entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Setup tests directory hierarchy for llmXive project."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )
    args = parser.parse_args()
    
    if args.verbose:
        print("Starting tests directory setup...")
    
    try:
        paths = setup_tests_directories()
        if args.verbose:
            print(f"Successfully created and verified directories: {paths}")
        print("Tests directory hierarchy setup complete.")
        return 0
    except Exception as e:
        print(f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
