"""
Script to initialize the project root directory for PROJ-298.
This script creates the root directory if it does not exist.
"""
import os
from pathlib import Path
import sys

def main():
    # Define the project root path relative to the repository root
    # The project is located at projects/PROJ-298-statistical-analysis-of-publicly-availab
    project_root = Path("projects/PROJ-298-statistical-analysis-of-publicly-availab")
    
    print(f"Ensuring project root directory exists: {project_root}")
    
    try:
        project_root.mkdir(parents=True, exist_ok=True)
        print(f"Success: Directory '{project_root}' is ready.")
        
        # Verify it's not empty by listing immediate children (if any)
        # Since T001b-e create subdirs, we expect them to exist if the pipeline runs sequentially
        # But for T001a specifically, we just ensure the root exists.
        if project_root.exists() and project_root.is_dir():
            print(f"Verified: {project_root} is a valid directory.")
            return 0
        else:
            print(f"Error: Failed to create or verify {project_root}", file=sys.stderr)
            return 1
            
    except PermissionError:
        print(f"Error: Permission denied when creating {project_root}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())