"""
Script to create the data directory structure with correct permissions.

This script creates the following directories at the repository root:
- data/
- data/raw/
- data/processed/
- data/logs/

All directories are created with 755 permissions (rwxr-xr-x).
"""
import os
import stat
import sys
from pathlib import Path
from typing import List

# Import from existing project API
from config import ensure_directories


def create_data_directories() -> List[Path]:
    """
    Create the data directory structure with 755 permissions.
    
    Returns:
        List[Path]: List of created directory paths
    """
    # Define directory structure relative to project root
    # We assume the script is run from the project root or code/ directory
    # and that data/ should be at the repository root
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root,
        data_root / "raw",
        data_root / "processed",
        data_root / "logs"
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            # Set permissions to 755 (rwxr-xr-x)
            os.chmod(dir_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path} with permissions 755")
        else:
            # Verify permissions even if directory exists
            current_mode = dir_path.stat().st_mode
            expected_mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
            
            if (current_mode & 0o777) != 0o755:
                os.chmod(dir_path, expected_mode)
                print(f"Fixed permissions for existing directory: {dir_path} to 755")
            else:
                print(f"Directory already exists with correct permissions: {dir_path}")
            created_dirs.append(dir_path)
    
    return created_dirs


def verify_directories() -> bool:
    """
    Verify that all required data directories exist with correct permissions.
    
    Returns:
        bool: True if all directories exist with 755 permissions, False otherwise
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    required_dirs = [
        data_root,
        data_root / "raw",
        data_root / "processed",
        data_root / "logs"
    ]
    
    all_valid = True
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            print(f"ERROR: Directory does not exist: {dir_path}")
            all_valid = False
            continue
        
        current_mode = dir_path.stat().st_mode
        if (current_mode & 0o777) != 0o755:
            print(f"ERROR: Directory has incorrect permissions: {dir_path} (expected 755, got {oct(current_mode & 0o777)})")
            all_valid = False
        else:
            print(f"OK: {dir_path} exists with permissions 755")
    
    return all_valid


def main():
    """Main entry point for the script."""
    print("Creating data directory structure...")
    created = create_data_directories()
    print(f"\nSuccessfully created {len(created)} directories.")
    
    print("\nVerifying directory structure...")
    if verify_directories():
        print("\nAll directories verified successfully.")
        return 0
    else:
        print("\nVerification failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
