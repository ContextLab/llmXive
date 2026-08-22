"""
Setup data directory structure for the llmXive project.

Creates the required directory hierarchy:
- data/raw: for immutable puzzles and raw datasets
- data/processed: for logs, results, and intermediate artifacts

Verifies that directories exist and are writable.
"""
import os
import sys
from pathlib import Path
from typing import List

def setup_data_directories(base_path: Path) -> List[Path]:
    """
    Create the required data directory structure.
    
    Args:
        base_path: The root directory for the project (where data/ should be created)
        
    Returns:
        List of created directory paths
        
    Raises:
        OSError: If directories cannot be created or are not writable
    """
    data_dir = base_path / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    directories = [data_dir, raw_dir, processed_dir]
    
    for directory in directories:
        # Create directory if it doesn't exist
        directory.mkdir(parents=True, exist_ok=True)
        
        # Verify the directory exists
        if not directory.exists():
            raise OSError(f"Failed to create directory: {directory}")
        
        # Verify the directory is a directory
        if not directory.is_dir():
            raise OSError(f"Path exists but is not a directory: {directory}")
        
        # Verify the directory is writable by attempting to create a test file
        test_file = directory / ".write_test"
        try:
            test_file.touch(exist_ok=True)
            test_file.unlink()
        except (OSError, IOError) as e:
            raise OSError(f"Directory is not writable: {directory}") from e
        
        print(f"Verified: {directory} exists and is writable")
    
    return directories

def main():
    """Main entry point for the script."""
    # Determine the project root (parent of code/)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Project root: {project_root}")
    print("Setting up data directory structure...")
    
    try:
        directories = setup_data_directories(project_root)
        print("\nData directory structure setup complete:")
        for d in directories:
            print(f"  - {d}")
        return 0
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
