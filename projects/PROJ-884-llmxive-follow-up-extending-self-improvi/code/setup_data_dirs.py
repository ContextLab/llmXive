"""
Setup script to create and verify the data directory hierarchy.
Creates data/raw and data/processed directories and verifies writability.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

def setup_data_directories(base_dir: Path) -> List[Path]:
    """
    Create the required data directory hierarchy.
    
    Args:
        base_dir: The root project directory.
        
    Returns:
        List of created directory paths.
        
    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    directories = [data_dir, raw_dir, processed_dir]
    
    for dir_path in directories:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
            except OSError as e:
                raise RuntimeError(f"Failed to create directory {dir_path}: {e}")
        
        # Verify writability by attempting to create a temporary file
        test_file = dir_path / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()  # Remove the test file
            print(f"Verified writability: {dir_path}")
        except IOError as e:
            raise RuntimeError(f"Directory {dir_path} is not writable: {e}")
    
    return directories

def main():
    parser = argparse.ArgumentParser(
        description="Setup data directory hierarchy for the project."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base project directory (default: current directory)"
    )
    
    args = parser.parse_args()
    base_path = Path(args.base_dir).resolve()
    
    print(f"Setting up data directories in: {base_path}")
    
    try:
        created_dirs = setup_data_directories(base_path)
        print("\nData directory hierarchy setup successful:")
        for d in created_dirs:
            print(f"  - {d}")
        return 0
    except RuntimeError as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
