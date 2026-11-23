"""
Task T001a: Create directory `code/` at repository root.

This script ensures the existence of the 'code' directory at the project root.
It is designed to be idempotent and can be run multiple times safely.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Main entry point to create the 'code' directory.
    """
    # Determine the project root (assuming this script is in code/setup/)
    # We go up two levels to reach the repository root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    code_dir = project_root / "code"
    
    try:
        if not code_dir.exists():
            code_dir.mkdir(parents=True, exist_ok=True)
            print(f"Successfully created directory: {code_dir}")
        else:
            print(f"Directory already exists: {code_dir}")
        
        # Verify it is a directory
        if code_dir.is_dir():
            print("Verification: 'code' is a valid directory.")
            return 0
        else:
            print(f"Error: {code_dir} exists but is not a directory.")
            return 1
            
    except OSError as e:
        print(f"Error creating directory {code_dir}: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
