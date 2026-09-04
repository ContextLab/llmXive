"""
Setup data directory structure for the llmXive project.

Creates the required directory hierarchy:
- data/raw: for immutable puzzles and raw datasets
- data/processed: for logs, results, and intermediate artifacts

Verifies that directories exist and are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple

# Define the required directory structure relative to project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
]

def setup_data_directories(base_path: Path) -> Tuple[bool, List[str]]:
    """
    Create the required data directory structure and verify writability.
    
    Args:
        base_path: The project root directory path.
        
    Returns:
        A tuple of (success: bool, errors: List[str])
    """
    errors = []
    created_dirs = []
    
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        
        # Create directory if it doesn't exist
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path))
                print(f"Created directory: {full_path}")
            else:
                print(f"Directory already exists: {full_path}")
        except OSError as e:
            errors.append(f"Failed to create directory {full_path}: {e}")
            continue
        
        # Verify writability
        try:
            # Try to create a temporary file to verify write permissions
            test_file = full_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            print(f"Verified writability: {full_path}")
        except (OSError, PermissionError) as e:
            errors.append(f"Directory {full_path} exists but is not writable: {e}")
    
    success = len(errors) == 0
    return success, errors

def main():
    """Main entry point for the data directory setup script."""
    parser = argparse.ArgumentParser(
        description="Setup data directory structure for llmXive project"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path("."),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Ensure base path is absolute for consistent reporting
    base_path = args.base_path.resolve()
    
    print(f"Setting up data directories in: {base_path}")
    print("-" * 50)
    
    success, errors = setup_data_directories(base_path)
    
    print("-" * 50)
    if success:
        print("✓ Data directory setup completed successfully.")
        print("  - data/raw: Ready for immutable puzzles")
        print("  - data/processed: Ready for logs and results")
        sys.exit(0)
    else:
        print("✗ Data directory setup failed with the following errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()