import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_data_directories(base_path: Path) -> List[Path]:
    """
    Create the required data directory hierarchy:
    - data/raw: for immutable puzzles and raw inputs
    - data/processed: for logs, results, and intermediate artifacts

    Verifies that directories exist and are writable.
    
    Args:
        base_path: The project root path where 'data' directory will be created.
        
    Returns:
        List of created directory paths.
        
    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    data_root = base_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    directories = [raw_dir, processed_dir]
    
    for directory in directories:
        # Create directory if it doesn't exist, including parents
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create directory {directory}: {e}")
        
        # Verify the directory exists
        if not directory.exists():
            raise RuntimeError(f"Directory {directory} was not created successfully.")
        
        if not directory.is_dir():
            raise RuntimeError(f"Path {directory} exists but is not a directory.")
        
        # Verify writability by attempting to create a temporary file
        test_file = directory / ".write_test"
        try:
            test_file.touch(exist_ok=True)
            test_file.unlink()  # Remove the test file
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Directory {directory} is not writable: {e}")
        
        print(f"Verified directory: {directory}")
    
    print(f"Data directory hierarchy created successfully at {data_root}")
    return directories

def main():
    """
    Command-line entry point for setting up data directories.
    """
    parser = argparse.ArgumentParser(
        description="Setup data directory hierarchy for the research project."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Path to the project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    try:
        dirs = setup_data_directories(args.project_root)
        print("SUCCESS: Data directories created and verified.")
        sys.exit(0)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()