"""
Script to create and verify the 'data/raw/' directory.
Implements idempotent creation and writability verification.
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path to ensure imports work if run as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def ensure_dir_with_writability_check(dir_path: Path) -> bool:
    """
    Ensures the directory exists and is writable.
    
    Args:
        dir_path: Path object of the directory to check/create.
        
    Returns:
        True if directory exists and is writable, False otherwise.
    """
    try:
        # Create directory if it doesn't exist (idempotent)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Verify writability by attempting a test write
        test_file = dir_path / ".write_test"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            # Clean up test file
            test_file.unlink()
            return True
        except (PermissionError, OSError) as e:
            print(f"ERROR: Directory {dir_path} exists but is not writable: {e}", file=sys.stderr)
            return False
            
    except OSError as e:
        print(f"ERROR: Failed to create directory {dir_path}: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Create and verify data/raw directory for project."
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recreation of directory (not recommended for production)"
    )
    args = parser.parse_args()

    print(f"Checking directory: {DATA_RAW_DIR}")
    
    if DATA_RAW_DIR.exists() and not args.force:
        print(f"Directory {DATA_RAW_DIR} already exists.")
    else:
        print(f"Creating directory: {DATA_RAW_DIR}")
        
    if ensure_dir_with_writability_check(DATA_RAW_DIR):
        print(f"SUCCESS: {DATA_RAW_DIR} exists and is writable.")
        sys.exit(0)
    else:
        print(f"FAILURE: {DATA_RAW_DIR} is missing or not writable.")
        sys.exit(1)

if __name__ == "__main__":
    main()