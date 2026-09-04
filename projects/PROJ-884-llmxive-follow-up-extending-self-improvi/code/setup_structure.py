"""
Setup script to create the code directory hierarchy.
This task (T001b) creates:
code/dataset
code/symbolic
code/bes
code/analysis
code/utils
And verifies they exist and are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

# Define the subdirectories to create under 'code/'
SUBDIRS = [
    "dataset",
    "symbolic",
    "bes",
    "analysis",
    "utils",
]

def setup_code_directories(root_dir: Path) -> bool:
    """
    Create the code directory hierarchy and verify writability.
    
    Args:
        root_dir: The project root directory.
        
    Returns:
        True if all directories were created and verified successfully.
        
    Raises:
        RuntimeError: If any directory cannot be created or is not writable.
    """
    code_dir = root_dir / "code"
    
    # Ensure the root code directory exists
    if not code_dir.exists():
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created root directory: {code_dir}")
    
    if not code_dir.is_dir():
        raise RuntimeError(f"{code_dir} exists but is not a directory.")
    
    # Check writability of the root code directory
    try:
        test_file = code_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (OSError, PermissionError) as e:
        raise RuntimeError(f"Root code directory {code_dir} is not writable: {e}")
    
    success = True
    for subdir_name in SUBDIRS:
        subdir_path = code_dir / subdir_name
        
        # Create the directory
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created subdirectory: {subdir_path}")
        
        if not subdir_path.is_dir():
            print(f"ERROR: {subdir_path} exists but is not a directory.")
            success = False
            continue
        
        # Verify writability
        try:
            test_file = subdir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            print(f"Verified writability: {subdir_path}")
        except (OSError, PermissionError) as e:
            print(f"ERROR: {subdir_path} is not writable: {e}")
            success = False
    
    if success:
        print("\n✓ All code directories created and verified writable.")
    else:
        print("\n✗ Some directories failed verification.")
        
    return success

def main():
    """Entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Create and verify the code directory hierarchy."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current working directory)",
    )
    args = parser.parse_args()
    
    success = setup_code_directories(args.root)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()