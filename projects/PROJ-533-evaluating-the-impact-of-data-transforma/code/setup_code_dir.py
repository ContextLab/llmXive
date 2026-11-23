"""
Setup script to create the 'code' directory and verify its existence.
This script fulfills task T001a.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the 'code' directory if it doesn't exist and verifies it.
    Exits with code 1 if verification fails.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    # Create directory
    try:
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory '{code_dir}' created or already exists.")
    except OSError as e:
        print(f"Error creating directory '{code_dir}': {e}")
        sys.exit(1)

    # Verify existence (simulating 'test -d code')
    if code_dir.is_dir():
        print(f"Verification successful: '{code_dir}' exists and is a directory.")
        sys.exit(0)
    else:
        print(f"Verification failed: '{code_dir}' does not exist or is not a directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()