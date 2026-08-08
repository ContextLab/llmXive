"""
Setup script to create and verify the 'data/processed' directory.
This task (T001d) ensures the directory exists for storing intermediate
and final processed data artifacts.
"""
import os
import sys
from pathlib import Path
from typing import Tuple

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def create_processed_directory() -> Tuple[bool, str]:
    """
    Creates the data/processed directory if it does not exist.
    
    Returns:
        Tuple[bool, str]: (Success status, Message)
    """
    try:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        return True, f"Directory created or verified: {PROCESSED_DIR}"
    except PermissionError:
        return False, f"Permission denied: Cannot create directory at {PROCESSED_DIR}"
    except Exception as e:
        return False, f"Error creating directory: {str(e)}"


def verify_processed_directory() -> Tuple[bool, str]:
    """
    Verifies that the data/processed directory exists and is a directory.
    
    Returns:
        Tuple[bool, str]: (Success status, Message)
    """
    if PROCESSED_DIR.exists() and PROCESSED_DIR.is_dir():
        return True, f"Verification successful: {PROCESSED_DIR} exists."
    else:
        return False, f"Verification failed: {PROCESSED_DIR} does not exist or is not a directory."


def main() -> int:
    """
    Main entry point for the script.
    Creates the directory and verifies its existence.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Target Directory: {PROCESSED_DIR}")
    
    # Step 1: Create
    success, msg = create_processed_directory()
    print(f"Create Result: {msg}")
    
    if not success:
        return 1
    
    # Step 2: Verify
    success, msg = verify_processed_directory()
    print(f"Verify Result: {msg}")
    
    if not success:
        return 1
        
    print("Task T001d completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
