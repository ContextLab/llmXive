"""
Setup script to create and verify data directories for the project.
Creates: data/raw/, data/processed/, data/models/
Verifies existence using os.path.isdir.
"""
import os
import sys
from pathlib import Path

# Project root is the directory containing this script's parent
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def setup_data_directories():
    """
    Create the required data subdirectories and verify their existence.
    
    Returns:
        bool: True if all directories were created and verified successfully.
        
    Raises:
        RuntimeError: If any directory creation fails or verification fails.
    """
    base_path = PROJECT_ROOT / "data"
    
    directories = [
        base_path / "raw",
        base_path / "processed",
        base_path / "models"
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        try:
            # Create directory with parents if needed, no error if exists
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created/Verified: {dir_path}")
        except OSError as e:
            raise RuntimeError(f"Failed to create directory {dir_path}: {e}")
    
    # Verification step: assert os.path.isdir returns True for each
    for dir_path in created_dirs:
        if not os.path.isdir(dir_path):
            raise RuntimeError(f"Verification failed: {dir_path} is not a valid directory.")
        
    print(f"Successfully created and verified {len(created_dirs)} data directories.")
    return True

def main():
    """Entry point for the script."""
    try:
        success = setup_data_directories()
        if success:
            print("Setup completed successfully.")
            sys.exit(0)
    except RuntimeError as e:
        print(f"Setup failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
